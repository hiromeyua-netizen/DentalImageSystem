/*
  ESP32-S3 LED PWM Controller
  Board: ESP32-S3-WROOM-1-N16R8 (Arduino core for ESP32)
  PWM pin: GPIO2 (IO02). DRIVE_ADC feedback: GPIO8 (IO08).

  Closed-loop: slider maps to CRTL voltage at LED driver (5V=OFF, 1.65V=ON max).
  DRIVE_ADC = V_ctrl * R11/(R5+R11) per schematic (56k + 100k divider).

  Serial (115200, newline-terminated):
    DIM:X | ON | OFF | STATUS | ADC | RECAL | HELP

  RECAL re-runs ADC-vs-PWM calibration if hardware changes.
*/

#include <Arduino.h>

// ---- Hardware ----
static const uint8_t PWM_PIN = 2;
static const uint8_t DRIVE_ADC_PIN = 8;
static const uint8_t PWM_CH = 0;
static const uint32_t PWM_FREQ = 5000;
static const uint8_t PWM_RES_BITS = 10;

// CRTL line targets (client spec): 5V = 0% (OFF), 1.65V = 100% (ON max)
static const float CTRL_VOLT_OFF = 5.00f;
static const float CTRL_VOLT_ON_MAX = 1.65f;

// Divider at DRIVE_ADC: R5=56k from CRTL, R11=100k to GND -> V_adc = V_ctrl * 100/(56+100)
static const float ADC_DIV = 100.0f / (56.0f + 100.0f);

// Closed-loop trim (few PWM updates per DIM — avoids visible “burst” from binary search)
static const uint8_t ADC_SAMPLES = 12;
static const uint16_t ADC_DEADBAND_MV = 35;
static const uint8_t TRIM_MAX_ITER = 5;
static const uint32_t TRIM_SETTLE_MS = 12;
static const int32_t TRIM_STEP_CAP = 72;

// Warm DIM: never let duty leave this band around last converged duty (stops
// wrong-sign trim from sprinting to duty=0 = full brightness on this hardware).
static const uint32_t WARM_DUTY_GUARD_MIN = 200;

// Calibration: two duties far enough apart for a reliable slope sign
static const uint8_t CAL_SETTLE_MS = 14;
static const uint32_t CAL_DUTY_SPAN = 220;

// ---- State ----
static uint8_t g_brightnessPct = 0;
static uint8_t g_lastNonZeroPct = 100;
static String g_line;
static bool g_pwmAttached = false;
static float g_lastTargetCtrlV = CTRL_VOLT_OFF;
static uint16_t g_lastTargetAdcMv = 0;
static uint32_t g_lastDuty = 0;
static bool g_adcRisesWithDuty = true;
static bool g_adcCalibrated = false;

static inline uint32_t maxDuty() {
  return (1UL << PWM_RES_BITS) - 1UL;
}

// Target CRTL voltage (V) for slider 0..100
static float sliderToCtrlVolt(uint8_t pct) {
  if (pct <= 0) return CTRL_VOLT_OFF;
  if (pct >= 100) return CTRL_VOLT_ON_MAX;
  const float t = (float)pct / 100.0f;
  return CTRL_VOLT_OFF - t * (CTRL_VOLT_OFF - CTRL_VOLT_ON_MAX);
}

// Expected DRIVE_ADC pin voltage (mV) for a given CRTL voltage
static uint16_t ctrlVoltToTargetAdcMv(float vCtrl) {
  if (vCtrl < 0.0f) vCtrl = 0.0f;
  if (vCtrl > CTRL_VOLT_OFF) vCtrl = CTRL_VOLT_OFF;
  const float vAdc = vCtrl * ADC_DIV;
  return (uint16_t)(vAdc * 1000.0f + 0.5f);
}

static uint32_t sampleAdcMv() {
#if !defined(ARDUINO_ARCH_ESP32)
  return 0;
#else
  uint32_t sum = 0;
  for (uint8_t i = 0; i < ADC_SAMPLES; ++i) {
    sum += (uint32_t)analogReadMilliVolts(DRIVE_ADC_PIN);
    delayMicroseconds(200);
  }
  return sum / ADC_SAMPLES;
#endif
}

// Learn whether higher LEDC duty increases or decreases ADC reading (hardware-dependent).
static void calibrateAdcVsDuty() {
#if !defined(ARDUINO_ARCH_ESP32)
  g_adcRisesWithDuty = true;
  g_adcCalibrated = false;
  return;
#endif
  const uint32_t hi = maxDuty();
  const uint32_t mid = hi / 2;
  const uint32_t half = CAL_DUTY_SPAN / 2;
  uint32_t dLo = (mid > half) ? (mid - half) : 0;
  uint32_t dHi = (mid + half < hi) ? (mid + half) : hi;
  if (dHi <= dLo + 40) {
    dLo = hi / 5;
    dHi = (hi * 4) / 5;
  }

  ledcWrite(PWM_CH, dLo);
  delay(CAL_SETTLE_MS);
  uint32_t aLo = sampleAdcMv();

  ledcWrite(PWM_CH, dHi);
  delay(CAL_SETTLE_MS);
  uint32_t aHi = sampleAdcMv();

  if (aHi > aLo + 25) {
    g_adcRisesWithDuty = true;
  } else if (aLo > aHi + 25) {
    g_adcRisesWithDuty = false;
  } else {
    // Ambiguous: prefer "higher duty -> higher ADC" (RC low-pass at sense is common).
    g_adcRisesWithDuty = true;
  }
  g_adcCalibrated = true;
}

// Open-loop duty: 0% -> high duty (high V / OFF), 100% -> low duty (low V / ON max).
static uint32_t openLoopDutyFromPct(uint8_t pct) {
  const uint32_t mx = maxDuty();
  if (pct <= 0) return mx;
  if (pct >= 100) return 0;
  return (uint32_t)((float)mx * (100.0f - (float)pct) / 100.0f + 0.5f);
}

static uint32_t warmDutyAllowance(uint8_t pct, uint8_t prevPct, uint32_t mx) {
  uint8_t span = pct > prevPct ? (uint8_t)(pct - prevPct) : (uint8_t)(prevPct - pct);
  uint32_t per = mx / 100u;
  if (per < 4) per = 4;
  uint32_t allow = (uint32_t)span * per + WARM_DUTY_GUARD_MIN;
  const uint32_t cap = mx / 2u;
  if (allow > cap) {
    allow = cap;
  }
  return allow;
}

static int32_t clampDutyToWindow(int32_t d, int32_t lo, int32_t hi) {
  if (d < lo) return lo;
  if (d > hi) return hi;
  return d;
}

// Few proportional trims from a sensible starting duty (no wide binary search).
// useFullDutyRange: after RECAL / first cal, or 0->ON — no tight guard around last duty.
static uint32_t findDutyForTargetAdcMv(
    uint16_t targetMv, uint8_t pct, bool useFullDutyRange, uint8_t prevPct) {
  const uint32_t mx = maxDuty();
  uint32_t duty = openLoopDutyFromPct(pct);
  int32_t guardLo = 0;
  int32_t guardHi = (int32_t)mx;

  if (g_lastDuty > 0 && prevPct > 0) {
    duty = (uint32_t)(((uint64_t)g_lastDuty * 2ULL + (uint64_t)duty) / 3ULL);
    if (duty > mx) duty = mx;
  }

  if (!useFullDutyRange && g_lastDuty > 0) {
    const uint32_t allow = warmDutyAllowance(pct, prevPct, mx);
    guardLo = clampDutyToWindow((int32_t)g_lastDuty - (int32_t)allow, 0, (int32_t)mx);
    guardHi = clampDutyToWindow((int32_t)g_lastDuty + (int32_t)allow, 0, (int32_t)mx);
    duty = (uint32_t)clampDutyToWindow((int32_t)duty, guardLo, guardHi);
  }

  for (uint8_t iter = 0; iter < TRIM_MAX_ITER; ++iter) {
    ledcWrite(PWM_CH, duty);
    delay(TRIM_SETTLE_MS);
    const uint32_t adcMv = sampleAdcMv();
    const int32_t err = (int32_t)targetMv - (int32_t)adcMv;
    const int32_t absErr = err < 0 ? -err : err;
    if (absErr <= (int32_t)ADC_DEADBAND_MV) {
      break;
    }

    int32_t step = (err * (int32_t)mx) / 500;
    if (step > TRIM_STEP_CAP) {
      step = TRIM_STEP_CAP;
    }
    if (step < -TRIM_STEP_CAP) {
      step = -TRIM_STEP_CAP;
    }
    if (step == 0) {
      step = (err > 0) ? 2 : -2;
    }
    if (!g_adcRisesWithDuty) {
      step = -step;
    }

    int32_t nd = (int32_t)duty + step;
    nd = clampDutyToWindow(nd, guardLo, guardHi);
    duty = (uint32_t)nd;
  }

  ledcWrite(PWM_CH, duty);
  delay(TRIM_SETTLE_MS);
  return duty;
}

static void applyBrightness(uint8_t pct) {
  const uint8_t prevApplied = g_brightnessPct;
  if (pct > 100) pct = 100;
  g_brightnessPct = pct;
  if (pct > 0) g_lastNonZeroPct = pct;

  if (pct == 0) {
    if (g_pwmAttached) {
      ledcDetachPin(PWM_PIN);
      g_pwmAttached = false;
    }
    pinMode(PWM_PIN, OUTPUT);
    digitalWrite(PWM_PIN, HIGH);
    g_lastTargetCtrlV = CTRL_VOLT_OFF;
    g_lastTargetAdcMv = ctrlVoltToTargetAdcMv(CTRL_VOLT_OFF);
    g_lastDuty = 0;
    return;
  }

  if (!g_pwmAttached) {
    ledcAttachPin(PWM_PIN, PWM_CH);
    g_pwmAttached = true;
  }

  bool ranCalibration = false;
  if (!g_adcCalibrated) {
    calibrateAdcVsDuty();
    ranCalibration = true;
  }

  const float vCtrl = sliderToCtrlVolt(pct);
  g_lastTargetCtrlV = vCtrl;
  g_lastTargetAdcMv = ctrlVoltToTargetAdcMv(vCtrl);

  const bool fromOff = (prevApplied == 0);
  const bool useFullDutyRange = fromOff || ranCalibration;
  g_lastDuty = findDutyForTargetAdcMv(g_lastTargetAdcMv, pct, useFullDutyRange, prevApplied);
}

static void printAdcPinVoltage() {
  const uint32_t adcMv = sampleAdcMv();
  const float vAdc = (float)adcMv / 1000.0f;
  float estCtrlV = 0.0f;
  if (ADC_DIV > 0.0001f) {
    estCtrlV = vAdc / ADC_DIV;
  }
  Serial.print("OK:ADC_PIN=");
  Serial.print(DRIVE_ADC_PIN);
  Serial.print(",MV=");
  Serial.print(adcMv);
  Serial.print(",V=");
  Serial.print(vAdc, 3);
  Serial.print(",EST_CTRL_V=");
  Serial.print(estCtrlV, 3);
  Serial.println();
}

static void printStatus() {
  const uint32_t adcMv = sampleAdcMv();
  Serial.print("STATUS:ON=");
  Serial.print(g_brightnessPct > 0 ? "1" : "0");
  Serial.print(",DIM=");
  Serial.print(g_brightnessPct);
  Serial.print(",TARGET_CTRL_V=");
  Serial.print(g_lastTargetCtrlV, 3);
  Serial.print(",TARGET_ADC_MV=");
  Serial.print(g_lastTargetAdcMv);
  Serial.print(",ADC_MV=");
  Serial.print(adcMv);
  Serial.print(",DUTY=");
  Serial.print(g_lastDuty);
  Serial.print(",ADC_CAL=");
  Serial.print(g_adcCalibrated ? (g_adcRisesWithDuty ? "1" : "0") : "0");
  Serial.print(",PIN=");
  Serial.print(PWM_PIN);
  Serial.print(",ADC_PIN=");
  Serial.print(DRIVE_ADC_PIN);
  Serial.print(",FREQ=");
  Serial.print(PWM_FREQ);
  Serial.print(",RES=");
  Serial.println(PWM_RES_BITS);
}

static bool parseDimCommand(const String &cmd, uint8_t &outPct) {
  int sep = cmd.indexOf(':');
  if (sep < 0) return false;
  String lhs = cmd.substring(0, sep);
  lhs.trim();
  lhs.toUpperCase();
  if (lhs != "DIM") return false;
  String rhs = cmd.substring(sep + 1);
  rhs.trim();
  if (rhs.length() == 0) return false;
  for (int i = 0; i < rhs.length(); ++i) {
    if (!isDigit((unsigned char)rhs[i])) return false;
  }
  int v = rhs.toInt();
  if (v < 0) v = 0;
  if (v > 100) v = 100;
  outPct = (uint8_t)v;
  return true;
}

static void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  String upper = cmd;
  upper.toUpperCase();

  uint8_t dimPct = 0;
  if (parseDimCommand(upper, dimPct)) {
    applyBrightness(dimPct);
    Serial.print("OK:DIM=");
    Serial.println(g_brightnessPct);
    return;
  }
  if (upper == "ON") {
    if (g_lastNonZeroPct == 0) g_lastNonZeroPct = 100;
    applyBrightness(g_lastNonZeroPct);
    Serial.print("OK:ON DIM=");
    Serial.println(g_brightnessPct);
    return;
  }
  if (upper == "OFF") {
    applyBrightness(0);
    Serial.println("OK:OFF");
    return;
  }
  if (upper == "STATUS") {
    printStatus();
    return;
  }
  if (upper == "ADC") {
    printAdcPinVoltage();
    return;
  }
  if (upper == "RECAL") {
    g_adcCalibrated = false;
    if (g_brightnessPct > 0) {
      applyBrightness(g_brightnessPct);
    }
    Serial.println("OK:RECAL");
    return;
  }
  if (upper == "HELP") {
    Serial.println("CMDS:DIM:X|ON|OFF|STATUS|ADC|RECAL|HELP");
    return;
  }
  Serial.print("ERR:UNKNOWN_CMD ");
  Serial.println(cmd);
}

void setup() {
  Serial.begin(115200);
  delay(100);

#if defined(ARDUINO_ARCH_ESP32)
  analogReadResolution(12);
#endif
  pinMode(DRIVE_ADC_PIN, INPUT);

  ledcSetup(PWM_CH, PWM_FREQ, PWM_RES_BITS);
  ledcAttachPin(PWM_PIN, PWM_CH);
  g_pwmAttached = true;

  applyBrightness(0);

  Serial.println("READY:ESP32_LED_CTRL");
  printStatus();
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (g_line.length() > 0) {
        handleCommand(g_line);
        g_line = "";
      }
    } else if (g_line.length() < 128) {
      g_line += c;
    }
  }
}
