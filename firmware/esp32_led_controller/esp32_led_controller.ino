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
// BuckPuck-style dim inputs typically behave best in the low-kHz range.
// Very high PWM can reduce effective dim range on some drivers.
static const uint32_t PWM_FREQ = 1000;  // 1 kHz
static const uint8_t PWM_RES_BITS = 10; // 0..1023, sufficient for smooth dimming
// Hardware polarity: true for active-low LED driver input (inverted brightness response).
static const bool PWM_ACTIVE_LOW = true;

// ---- State ----
static uint8_t g_brightnessPct = 0;      // 0..100 currently applied
static uint8_t g_lastNonZeroPct = 100;   // used by ON
static String g_line;

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
  ledcWrite(PWM_CH, pctToDuty(pct));
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

