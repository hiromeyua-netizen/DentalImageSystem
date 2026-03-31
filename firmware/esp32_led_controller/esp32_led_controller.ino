/*
  ESP32-S3 LED PWM Controller
  Board: ESP32-S3-WROOM-1-N16R8 (Arduino core for ESP32)
  PWM pin: GPIO2 (IO02 from schematic)

  Serial protocol (115200 baud, newline-terminated):
    DIM:X      -> set brightness 0..100
    ON         -> restore last non-zero level (or 100 if none)
    OFF        -> set 0
    STATUS     -> report current state
    HELP       -> command list

  Examples:
    DIM:35
    ON
    OFF
    STATUS
*/

#include <Arduino.h>

// ---- Hardware ----
static const uint8_t PWM_PIN = 2;       // IO02
static const uint8_t PWM_CH = 0;
// Per schematic design note: 5 kHz PWM into dimming front-end.
static const uint32_t PWM_FREQ = 5000;  // 5 kHz
static const uint8_t PWM_RES_BITS = 10; // 0..1023, sufficient for smooth dimming
// Hardware polarity: true for active-low LED driver input (inverted brightness response).
static const bool PWM_ACTIVE_LOW = true;
// Some drivers achieve true OFF only when control pin is high-impedance (released),
// letting an external pull-up define the OFF level.
static const bool OFF_USES_HIZ = false;
// Effective dimming span from client validation:
// user 0..55 changes, above that saturates (full-on region).
// Map user 1..100 into 1..55 to keep slider meaningful end-to-end.
static const uint8_t EFFECTIVE_DIM_MAX_PCT = 55;

// ---- State ----
static uint8_t g_brightnessPct = 0;      // 0..100 currently applied
static uint8_t g_lastNonZeroPct = 100;   // used by ON
static String g_line;
static bool g_pwmAttached = false;

static uint8_t mapUserPctToDrivePct(uint8_t userPct) {
  if (userPct <= 0) return 0;
  if (userPct >= 100) return EFFECTIVE_DIM_MAX_PCT;
  long v = map((long)userPct, 1L, 100L, 1L, (long)EFFECTIVE_DIM_MAX_PCT);
  if (v < 1) v = 1;
  if (v > EFFECTIVE_DIM_MAX_PCT) v = EFFECTIVE_DIM_MAX_PCT;
  return (uint8_t)v;
}

static uint32_t pctToDuty(uint8_t pct) {
  const uint32_t maxDuty = (1UL << PWM_RES_BITS) - 1UL;
  // Guarantee electrical extremes at endpoints.
  if (pct == 0) {
    return PWM_ACTIVE_LOW ? maxDuty : 0;
  }
  if (pct >= 100) {
    return PWM_ACTIVE_LOW ? 0 : maxDuty;
  }

  uint32_t duty = (uint32_t)((maxDuty * (uint32_t)pct) / 100UL);
  if (PWM_ACTIVE_LOW) {
    duty = maxDuty - duty;
  }
  return duty;
}

static void applyBrightness(uint8_t pct) {
  if (pct > 100) pct = 100;
  g_brightnessPct = pct;
  if (pct > 0) g_lastNonZeroPct = pct;

  // Force hard logic levels at endpoints to guarantee true OFF / MAX.
  // Some LED drivers do not fully extinguish at PWM endpoint duty alone.
  if (pct == 0 || pct == 100) {
    if (g_pwmAttached) {
      ledcDetachPin(PWM_PIN);
      g_pwmAttached = false;
    }
    if (pct == 0) {
      // OFF level: optionally release pin (Hi-Z) for true driver shutdown.
      if (OFF_USES_HIZ) {
        pinMode(PWM_PIN, INPUT);
      } else {
        pinMode(PWM_PIN, OUTPUT);
        digitalWrite(PWM_PIN, PWM_ACTIVE_LOW ? HIGH : LOW);
      }
    } else { // pct == 100
      // MAX level depends on active polarity.
      pinMode(PWM_PIN, OUTPUT);
      digitalWrite(PWM_PIN, PWM_ACTIVE_LOW ? LOW : HIGH);
    }
    return;
  }

  // Mid-range uses PWM dimming.
  if (!g_pwmAttached) {
    ledcAttachPin(PWM_PIN, PWM_CH);
    g_pwmAttached = true;
  }
  const uint8_t drivePct = mapUserPctToDrivePct(pct);
  ledcWrite(PWM_CH, pctToDuty(drivePct));
}

static void printStatus() {
  Serial.print("STATUS:ON=");
  Serial.print(g_brightnessPct > 0 ? "1" : "0");
  Serial.print(",DIM=");
  Serial.print(g_brightnessPct);
  Serial.print(",PIN=");
  Serial.print(PWM_PIN);
  Serial.print(",FREQ=");
  Serial.print(PWM_FREQ);
  Serial.print(",RES=");
  Serial.println(PWM_RES_BITS);
}

static bool parseDimCommand(const String &cmd, uint8_t &outPct) {
  // Expects DIM:X
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

  if (upper == "HELP") {
    Serial.println("CMDS:DIM:X|ON|OFF|STATUS|HELP");
    return;
  }

  Serial.print("ERR:UNKNOWN_CMD ");
  Serial.println(cmd);
}

void setup() {
  Serial.begin(115200);
  delay(100);

  ledcSetup(PWM_CH, PWM_FREQ, PWM_RES_BITS);
  ledcAttachPin(PWM_PIN, PWM_CH);
  g_pwmAttached = true;
  applyBrightness(0); // safe startup: LEDs off

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
    } else {
      if (g_line.length() < 128) {
        g_line += c;
      }
    }
  }
}

