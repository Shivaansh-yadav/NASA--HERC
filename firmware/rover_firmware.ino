/*
  Team Vansh HERC 2027: rover reference firmware
  Target board: Seeed Studio XIAO ESP32S3 (ESP32 Arduino framework)

  Implements the onboard half of the analyses in this repository:
    * 4 channel ESC PWM (LEDC), exponential slew limiting, link loss failsafe
    * wheel encoder counting on interrupts, IMU (MPU-6050 class) over I2C
    * wheel slip detector from Analysis 5 deployed as a fixed threshold with the
      trained coefficients (AUC 0.99, accuracy 95.5% on the synthetic set)
    * granular jamming gripper pump control, current plateau = jam confirmed (Analysis 7)
    * 10 Hz UDP JSON telemetry for the laptop dashboard
    * battery monitor on an ADC divider (6S pack)

  Wiring is deliberately generic; adjust PIN_* defines to the actual harness.
  No external libraries: only the ESP32 Arduino core (WiFi, Wire, LEDC).
*/

#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <math.h>

#include "rover_config.h"

/* ---------------- state ---------------- */
enum RoverState { STATE_IDLE, STATE_DRIVE, STATE_PIT, STATE_GRIPPER };
static RoverState state = STATE_IDLE;

static WiFiUDP udp;
static float cmdMix[4] = {0, 0, 0, 0};      /* commanded wheel effort, 0..1 */
static float escCmd[4] = {0, 0, 0, 0};      /* slew limited effort          */
static volatile long encTicks[4] = {0, 0, 0, 0};
static float wheelSpeed[4] = {0, 0, 0, 0};  /* m/s, low passed */
static float bodySpeed = 0.0f;              /* average wheel speed as body reference */
static float pitchRate = 0.0f;              /* rad/s, gyro pitch  */
static float pitchRateLP = 0.0f;            /* rad/s, low passed  */
static float battVolts = 0.0f;
static bool  slipLatch = false;
static bool  jamConfirmed = false;
static float driveCmd = 0.0f;               /* throttle, 0..1 */
static float turnCmd  = 0.0f;               /* tank steering, -1..1 */
static uint32_t lastTele = 0, lastTick = 0, pumpStart = 0;

static void IRAM_ATTR encIsr0() { encTicks[0]++; }
static void IRAM_ATTR encIsr1() { encTicks[1]++; }
static void IRAM_ATTR encIsr2() { encTicks[2]++; }
static void IRAM_ATTR encIsr3() { encTicks[3]++; }

static float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

static void escWrite(int ch, float effort) {
  float us = ESC_MIN_US + (ESC_MAX_US - ESC_MIN_US) * clampf(effort, 0.0f, 1.0f);
  ledcWrite(ch, (int)(us / 20000.0f * 4096.0f));  /* 50 Hz, 12 bit LEDC */
}

/* slip probability from the trained logistic model */
static float slipProb(float dv, float pitchRes) {
  float z = SLIP_B0 + SLIP_B1 * dv + SLIP_B2 * pitchRes;
  return 1.0f / (1.0f + expf(-z));
}

static void readImu() {
  /* MPU-6050 class IMU at 0x68: burst read gyro registers 0x43..0x44 (pitch axis) */
  Wire.beginTransmission(0x68);
  Wire.write(0x43);
  if (Wire.endTransmission(false) == 0 && Wire.requestFrom(0x68, 2) == 2) {
    int16_t raw = (int16_t)((Wire.read() << 8) | Wire.read());
    pitchRate = (float)raw / 32768.0f * 250.0f * PI / 180.0f;  /* +-250 dps range */
  }
}

static void controlTick() {
  /* speeds */
  for (int i = 0; i < 4; i++) {
    float v = (float)encTicks[i] / ENC_TICKS_REV * 2.0f * PI * (WHEEL_DIAM_M / 2.0f) / 0.02f;
    encTicks[i] = 0;
    wheelSpeed[i] += 0.4f * (v - wheelSpeed[i]);           /* low pass */
  }
  bodySpeed = 0.25f * (wheelSpeed[0] + wheelSpeed[1] + wheelSpeed[2] + wheelSpeed[3]);
  pitchRateLP += 0.3f * (pitchRate - pitchRateLP);

  /* tank steering mix */
  float left  = clampf(driveCmd - 0.5f * turnCmd, 0.0f, 1.0f);
  float right = clampf(driveCmd + 0.5f * turnCmd, 0.0f, 1.0f);
  cmdMix[0] = left; cmdMix[1] = right; cmdMix[2] = left; cmdMix[3] = right;

  /* slip detection, Analysis 5 deployed: dv = wheel vs body, pitch residual = gyro vs low pass */
  float dvMax = 0.0f;
  for (int i = 0; i < 4; i++) dvMax = fmaxf(dvMax, wheelSpeed[i] - bodySpeed);
  float pitchRes = pitchRate - pitchRateLP;
  float pSlip = slipProb(dvMax, pitchRes);
  if (pSlip >= SLIP_TH) {
    slipLatch = true;                                      /* cut torque, Analysis 5 */
  } else if (slipLatch && pSlip < 0.35f) {
    slipLatch = false;                                     /* re-engage with hysteresis */
  }
  float gate = slipLatch ? 0.25f : 1.0f;

  /* slew limit + apply */
  for (int i = 0; i < 4; i++) {
    float target = cmdMix[i] * gate;
    float d = target - escCmd[i];
    d = clampf(d, -SLEW_PER_TICK, SLEW_PER_TICK);
    escCmd[i] += d;
    escWrite(i, escCmd[i]);
  }
}

static void gripperTick(bool pumpOn) {
  digitalWrite(PIN_PUMP, pumpOn ? HIGH : LOW);
  if (pumpOn) {
    float ma = 4095.0f > 0 ? (analogReadMilliVolts(PIN_PUMP_IS) / 500.0f) * 1000.0f : 0;
    if (ma >= PUMP_JAM_MA) jamConfirmed = true;            /* plateau: granular jam set */
    if (millis() - pumpStart > PUMP_MAX_MS) jamConfirmed = false;
  } else {
    jamConfirmed = false;
    pumpStart = millis();
  }
}

static void telemetry() {
  if (millis() - lastTele < TELE_MS) return;
  lastTele = millis();
  char buf[384];
  int n = snprintf(buf, sizeof(buf),
    "{\"t\":%lu,\"state\":%d,\"batt\":%.2f,\"w\":[%.2f,%.2f,%.2f,%.2f],"
    "\"body\":%.2f,\"pitch\":%.3f,\"slip\":%d,\"jam\":%d,"
    "\"esc\":[%.2f,%.2f,%.2f,%.2f]}",
    (unsigned long)(millis() / 1000), (int)state, battVolts,
    wheelSpeed[0], wheelSpeed[1], wheelSpeed[2], wheelSpeed[3],
    bodySpeed, pitchRate, (int)slipLatch, (int)jamConfirmed,
    escCmd[0], escCmd[1], escCmd[2], escCmd[3]);
  if (n > 0) udp.beginPacket(DASH_IP, DASH_PORT), udp.write((const uint8_t*)buf, n), udp.endPacket();
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) {
    ledcSetup(i, 50, 12);                                  /* 50 Hz, 12 bit */
    ledcAttachPin(PIN_ESC[i], i);
    pinMode(PIN_ENC[i], INPUT_PULLUP);
  }
  attachInterrupt(digitalPinToInterrupt(PIN_ENC[0]), encIsr0, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC[1]), encIsr1, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC[2]), encIsr2, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC[3]), encIsr3, RISING);
  pinMode(PIN_PUMP, OUTPUT);
  digitalWrite(PIN_PUMP, LOW);
  analogReadResolution(12);
  Wire.begin(PIN_SDA, PIN_SCL);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(WIFI_SSID, WIFI_PASS);
  udp.begin(8899);
}

void loop() {
  uint32_t now = millis();
  if (now - lastTick >= 20) {                              /* 50 Hz control tick */
    lastTick = now;
    readImu();
    battVolts = analogReadMilliVolts(PIN_BATT) / 1000.0f * 11.0f;  /* divider */
    controlTick();
    gripperTick(state == STATE_GRIPPER);
    telemetry();
  }
}
