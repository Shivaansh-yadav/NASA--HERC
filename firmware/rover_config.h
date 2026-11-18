/*
  Team Vansh HERC 2027: rover configuration
  Single source of truth for pins, mechanical constants and the trained
  slip-detector coefficients. Included by rover_firmware.ino.
  Human-readable mirror: configs/rover_params.yaml
*/
#ifndef ROVER_CONFIG_H
#define ROVER_CONFIG_H

#include <Arduino.h>

/* ---- trained slip detector (Analysis 5; see notebooks/analysis_walkthrough.ipynb) ----
   logistic model: p = 1 / (1 + exp(-(B0 + B1*dv + B2*pitchRes)))
   trained coefficients, seeded synthetic set of 4000 samples, AUC 0.99, accuracy 95.5% */
constexpr float SLIP_B0 = -3.1406f;
constexpr float SLIP_B1 =  7.2035f;   /* feature 1: dv, wheel minus body speed (m/s) */
constexpr float SLIP_B2 = -2.9114f;   /* feature 2: IMU pitch rate residual (rad/s)  */
constexpr float SLIP_TH =  0.5f;      /* decision threshold on p                     */
constexpr float SLIP_RELEASE_TH = 0.35f;  /* re-engage below this (hysteresis) */

/* ---- pins (Seeed Studio XIAO ESP32S3) ---- */
constexpr int PIN_ESC[4]   = {D1, D2, D3, D4};  /* FL FR RL RR, 50 Hz servo PWM */
constexpr int PIN_ENC[4]   = {D5, D6, D7, D8};  /* single channel per wheel     */
constexpr int PIN_PUMP     = D9;                /* gripper pump relay           */
constexpr int PIN_PUMP_IS  = A2;                /* pump current sense, ADC      */
constexpr int PIN_BATT     = A1;                /* battery divider, ADC         */
constexpr int PIN_SDA      = 5;
constexpr int PIN_SCL      = 6;

/* ---- drivetrain ---- */
constexpr float WHEEL_DIAM_M  = 0.10f;
constexpr float ENC_TICKS_REV = 12.0f;
constexpr float ESC_MIN_US    = 1000.0f;
constexpr float ESC_MAX_US    = 2000.0f;
constexpr float SLEW_PER_TICK = 0.02f;   /* max command change per 20 ms tick */

/* ---- gripper (Analysis 7) ---- */
constexpr float   PUMP_JAM_MA = 950.0f;  /* current plateau indicating jam */
constexpr uint32_t PUMP_MAX_MS = 8000;   /* absolute pump timeout          */

/* ---- control loop ---- */
constexpr uint32_t TICK_MS  = 20;        /* 50 Hz control tick  */
constexpr uint32_t TELE_MS  = 100;       /* 10 Hz telemetry     */

#endif  /* ROVER_CONFIG_H */
