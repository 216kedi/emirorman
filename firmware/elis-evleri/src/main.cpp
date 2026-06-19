// =============================================================================
//  Elis Evleri — ESP32 akıllı bina firmware'i
//
//  Giriş katı (MODE_GROUND):
//    * PIR1 (GPIO25)        -> girişteki iç içe dikdörtgenler SIRAYLA yanar
//    * PIR2/PIR3 (26/27)    -> koridorun iki ucu; ikisi de koridoru FADE IN/OUT eder
//    * Duman (18) / Gaz (19)-> güvenlik rölesi (siren) + kırmızı LED + WhatsApp (backend)
//  Üst kat (MODE_UPPER):
//    * PIR2/PIR3 (26/27)    -> koridoru FADE IN/OUT eder (duman/gaz/röle yok)
//
//  Tasarım: tamamen non-blocking (millis tabanlı). Yangın/gaz alarmında RÖLE ve LED
//  ANINDA ve YEREL çalışır (WiFi/backend'e bağlı değildir); WhatsApp en iyi çaba ile
//  ayrıca gönderilir.
// =============================================================================
#include <Arduino.h>
#include <FastLED.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

#include "config.h"

static CRGB leds[NUM_LEDS];
static const CRGB AMBIENT = CRGB(AMBIENT_R, AMBIENT_G, AMBIENT_B);
static const CRGB ALARM = CRGB(ALARM_R, ALARM_G, ALARM_B);

// ---- Aydınlatma durumu ----
static uint8_t corridorBri = 0;
static uint32_t lastCorridorMotion = 0;

#if ENTRANCE_ENABLED
static uint8_t rectBri[NUM_RECTANGLES] = {0};
static int entranceActiveCount = 0;
static uint32_t lastEntranceStep = 0;
static uint32_t lastEntranceMotion = 0;
#endif

// ---- Güvenlik durumu ----
#if SAFETY_ENABLED
static bool alarmActive = false;
static bool alarmBlinkOn = false;
static uint32_t lastBlink = 0;
static uint32_t smokeActiveSince = 0;
static uint32_t gasActiveSince = 0;
static uint32_t alarmClearSince = 0;
static uint32_t lastSmokeAlertMs = 0;
static uint32_t lastGasAlertMs = 0;
#endif

static uint32_t lastFrame = 0;
static uint32_t lastWifiTry = 0;

// ----------------------------------------------------------------- yardımcılar
static inline bool readActive(uint8_t pin, uint8_t activeLevel) {
    return digitalRead(pin) == activeLevel;
}

static uint8_t stepSize(uint32_t fadeMs) {
    long s = (255L * FRAME_MS) / (long)fadeMs;
    if (s < 1) s = 1;
    if (s > 255) s = 255;
    return (uint8_t)s;
}

static void stepToward(uint8_t &cur, uint8_t target, uint8_t step) {
    if (cur < target)
        cur = (uint8_t)((target - cur > step) ? cur + step : target);
    else if (cur > target)
        cur = (uint8_t)((cur - target > step) ? cur - step : target);
}

// ----------------------------------------------------------------- WiFi
static void maintainWifi(uint32_t now) {
    if (WiFi.status() == WL_CONNECTED) return;
    if (now - lastWifiTry >= WIFI_RETRY_MS) {
        lastWifiTry = now;
        WiFi.disconnect();
        WiFi.begin(WIFI_SSID, WIFI_PASS);
        Serial.println("[elis] wifi reconnect...");
    }
}

// ----------------------------------------------------------------- backend POST
#if SAFETY_ENABLED
static bool postAlert(const char *sensor, const char *state) {
    if (WiFi.status() != WL_CONNECTED) return false;

    char body[224];
    snprintf(body, sizeof(body),
             "{\"device_id\":\"%s\",\"floor\":\"%s\",\"sensor\":\"%s\",\"state\":\"%s\"}",
             DEVICE_ID, FLOOR_NUMBER, sensor, state);

    HTTPClient http;
    bool https = strncmp(BACKEND_URL, "https", 5) == 0;
    bool begun;
    WiFiClientSecure secure;
    WiFiClient plain;
    if (https) {
        secure.setInsecure();  // basitlik için; üretimde kök sertifika sabitlemesi önerilir
        begun = http.begin(secure, BACKEND_URL);
    } else {
        begun = http.begin(plain, BACKEND_URL);
    }
    if (!begun) return false;

    http.addHeader("Content-Type", "application/json");
    http.addHeader("x-api-key", API_KEY);
    int code = http.POST((uint8_t *)body, strlen(body));
    http.end();

    Serial.printf("[elis] POST %s/%s -> %d\n", sensor, state, code);
    return code >= 200 && code < 300;
}

static bool sendAlertWithRetry(const char *sensor, const char *state) {
    for (int i = 0; i < ALERT_MAX_RETRIES; i++) {
        if (postAlert(sensor, state)) return true;
        delay(ALERT_RETRY_DELAY_MS);
    }
    return false;
}
#endif  // SAFETY_ENABLED

// ----------------------------------------------------------------- hareket
static void updateMotion(uint32_t now) {
    if (readActive(PIR2_PIN, PIR_ACTIVE_LEVEL) || readActive(PIR3_PIN, PIR_ACTIVE_LEVEL)) {
        lastCorridorMotion = now;
    }
#if ENTRANCE_ENABLED
    if (readActive(PIR1_PIN, PIR_ACTIVE_LEVEL)) {
        lastEntranceMotion = now;
    }
#endif
}

// ----------------------------------------------------------------- güvenlik
#if SAFETY_ENABLED
static void handleSafety(uint32_t now) {
    bool smoke = readActive(SMOKE_PIN, SMOKE_ACTIVE_LEVEL);
    bool gas = readActive(GAS_PIN, GAS_ACTIVE_LEVEL);

    if (smoke) {
        if (smokeActiveSince == 0) smokeActiveSince = now;
    } else {
        smokeActiveSince = 0;
    }
    if (gas) {
        if (gasActiveSince == 0) gasActiveSince = now;
    } else {
        gasActiveSince = 0;
    }

    bool smokeAlarm = smokeActiveSince != 0 && (now - smokeActiveSince) >= SAFETY_DEBOUNCE_MS;
    bool gasAlarm = gasActiveSince != 0 && (now - gasActiveSince) >= SAFETY_DEBOUNCE_MS;

    if (smokeAlarm || gasAlarm) {
        alarmClearSince = 0;
        if (!alarmActive) {
            alarmActive = true;
            digitalWrite(RELAY_PIN, RELAY_ACTIVE_LEVEL);  // YEREL siren — ağdan bağımsız
            Serial.println("[elis] ALARM!");
        }
        if (smokeAlarm && (lastSmokeAlertMs == 0 || now - lastSmokeAlertMs >= ALERT_COOLDOWN_MS)) {
            sendAlertWithRetry("smoke", "alarm");
            lastSmokeAlertMs = now;
        }
        if (gasAlarm && (lastGasAlertMs == 0 || now - lastGasAlertMs >= ALERT_COOLDOWN_MS)) {
            sendAlertWithRetry("gas", "alarm");
            lastGasAlertMs = now;
        }
    } else if (alarmActive) {
        if (alarmClearSince == 0) alarmClearSince = now;
        if (now - alarmClearSince >= ALARM_CLEAR_HOLD_MS) {
            alarmActive = false;
            digitalWrite(RELAY_PIN, RELAY_IDLE_LEVEL);
            lastSmokeAlertMs = 0;
            lastGasAlertMs = 0;
            Serial.println("[elis] alarm cleared");
        }
    }
}
#endif  // SAFETY_ENABLED

// ----------------------------------------------------------------- animasyon
static void advance(uint32_t now) {
#if SAFETY_ENABLED
    if (alarmActive) {
        if (now - lastBlink >= ALARM_BLINK_MS) {
            lastBlink = now;
            alarmBlinkOn = !alarmBlinkOn;
        }
        return;  // alarm sırasında ambient aydınlatma durdurulur
    }
#endif

    // Koridor: PIR2/PIR3 hareketinden HOLD süresi içindeyse açık.
    bool corridorOn = (now - lastCorridorMotion) < CORRIDOR_HOLD_MS;
    uint8_t corridorTarget = corridorOn ? 255 : 0;
    uint8_t cStep = corridorTarget > corridorBri ? stepSize(CORRIDOR_FADE_IN_MS)
                                                 : stepSize(CORRIDOR_FADE_OUT_MS);
    stepToward(corridorBri, corridorTarget, cStep);

#if ENTRANCE_ENABLED
    // Giriş dikdörtgenleri: hareket varken sırayla artar, gidince sırayla azalır.
    bool entranceOn = (now - lastEntranceMotion) < ENTRANCE_HOLD_MS;
    int targetCount = entranceOn ? NUM_RECTANGLES : 0;
    if (now - lastEntranceStep >= ENTRANCE_STEP_MS) {
        lastEntranceStep = now;
        if (entranceActiveCount < targetCount) entranceActiveCount++;
        else if (entranceActiveCount > targetCount) entranceActiveCount--;
    }
    uint8_t rStep = stepSize(RECT_FADE_MS);
    for (int r = 0; r < NUM_RECTANGLES; r++) {
        uint8_t t = (r < entranceActiveCount) ? 255 : 0;
        stepToward(rectBri[r], t, rStep);
    }
#endif
}

static void compose() {
    fill_solid(leds, NUM_LEDS, CRGB::Black);

#if SAFETY_ENABLED
    if (alarmActive) {
        if (alarmBlinkOn) fill_solid(leds, NUM_LEDS, ALARM);
        return;
    }
#endif

    // Koridor bölgesi
    for (int i = 0; i < CORRIDOR_COUNT; i++) {
        int idx = CORRIDOR_START + i;
        if (idx >= 0 && idx < NUM_LEDS) {
            CRGB c = AMBIENT;
            c.nscale8_video(corridorBri);
            leds[idx] = c;
        }
    }

#if ENTRANCE_ENABLED
    // Giriş dikdörtgenleri
    for (int r = 0; r < NUM_RECTANGLES; r++) {
        int start = RECT_RANGES[r][0];
        int count = RECT_RANGES[r][1];
        CRGB c = AMBIENT;
        c.nscale8_video(rectBri[r]);
        for (int i = 0; i < count; i++) {
            int idx = start + i;
            if (idx >= 0 && idx < NUM_LEDS) leds[idx] = c;
        }
    }
#endif
}

// ----------------------------------------------------------------- setup/loop
void setup() {
    Serial.begin(115200);
    delay(100);

    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(MASTER_BRIGHTNESS);
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();

    pinMode(PIR2_PIN, PIR_PINMODE);
    pinMode(PIR3_PIN, PIR_PINMODE);
#if ENTRANCE_ENABLED
    pinMode(PIR1_PIN, PIR_PINMODE);
#endif
#if SAFETY_ENABLED
    pinMode(SMOKE_PIN, SMOKE_PINMODE);
    pinMode(GAS_PIN, GAS_PINMODE);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, RELAY_IDLE_LEVEL);
#endif

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    Serial.printf("[elis] boot — mode=%s floor=%s\n",
                  (FLOOR_MODE == MODE_GROUND) ? "GROUND" : "UPPER", FLOOR_NUMBER);
}

void loop() {
    uint32_t now = millis();

    maintainWifi(now);
    updateMotion(now);
#if SAFETY_ENABLED
    handleSafety(now);
#endif

    if (now - lastFrame >= FRAME_MS) {
        lastFrame = now;
        advance(now);
        compose();
        FastLED.show();
    }
}
