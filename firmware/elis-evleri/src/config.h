// =============================================================================
//  Elis Evleri — ESP32 yapılandırması (TÜM AYARLAR BURADA)
//  Bu dosyayı her kat için düzenleyip cihaza yükleyin.
// =============================================================================
#pragma once

// ------------------------------------------------------------------ KAT MODU
#define MODE_GROUND 0   // Giriş katı: PIR1 girişteki dikdörtgenler + PIR2/PIR3 koridor + duman/gaz
#define MODE_UPPER  1   // Üst kat:    koridorun iki ucunda 2 PIR -> koridor fade in/out

#define FLOOR_MODE     MODE_GROUND     // <-- her kat için MODE_GROUND ya da MODE_UPPER
#define FLOOR_NUMBER   "0"             // mesajda görünecek kat no ("0", "1", "2"...)
#define DEVICE_ID      "elis-giris-1"  // bu cihaza özel kimlik

// Aşağıdakiler FLOOR_MODE'dan türetilir (normalde değiştirmeyin).
#define ENTRANCE_ENABLED (FLOOR_MODE == MODE_GROUND)  // girişteki dikdörtgen animasyonu
#define SAFETY_ENABLED   (FLOOR_MODE == MODE_GROUND)  // duman/gaz + güvenlik rölesi

// ------------------------------------------------------------------ PINLER (ekteki tabloyla birebir)
#define LED_PIN    4    // Adreslenebilir LED (WS2812) veri hattı / durum göstergesi
#define RELAY_PIN  23   // Güvenlik rölesi (güç/siren kontrolü)
#define PIR1_PIN   25   // 1. PIR — giriş (dikdörtgenler)         [yalnızca giriş katı]
#define PIR2_PIN   26   // 2. PIR — koridor ucu A
#define PIR3_PIN   27   // 3. PIR — koridor ucu B
#define GAS_PIN    19   // Gaz sensörü (lojik kart sinyali)        [giriş katı]
#define SMOKE_PIN  18   // Duman dedektörü (yangın röle sinyali)   [giriş katı]

// ------------------------------------------------------------------ LED ŞERİT
#define LED_TYPE     WS2812B
#define COLOR_ORDER  GRB
#define NUM_LEDS     76     // şeritteki TOPLAM LED sayısı (giriş + koridor)
#define MASTER_BRIGHTNESS 200  // genel parlaklık 0..255

// Ambient (sıcak beyaz) ve alarm (kırmızı) renkleri
#define AMBIENT_R 255
#define AMBIENT_G 160
#define AMBIENT_B 70
#define ALARM_R   255
#define ALARM_G   0
#define ALARM_B   0

// --- Koridor bölgesi (şerit üzerindeki indeks aralığı) --------------------
// Üst katta tüm şerit koridordur: CORRIDOR_START 0, CORRIDOR_COUNT NUM_LEDS yapın.
#define CORRIDOR_START 56
#define CORRIDOR_COUNT 20

// --- Giriş "iç içe dikdörtgenler" (yalnızca giriş katı) -------------------
// Her satır bir dikdörtgen: { başlangıç_indeksi, led_sayısı }. Dıştan içe sırayla yanar.
// Bina ölçülünce gerçek değerlerle güncelleyin.
#define NUM_RECTANGLES 4
static const int RECT_RANGES[NUM_RECTANGLES][2] = {
    {0, 20},   // 1. (en dış) dikdörtgen
    {20, 16},  // 2. dikdörtgen
    {36, 12},  // 3. dikdörtgen
    {48, 8},   // 4. (en iç) dikdörtgen
};

// ------------------------------------------------------------------ GİRİŞ SEVİYELERİ
// PIR modülleri tipik olarak hareket halinde HIGH verir.
#define PIR_PINMODE       INPUT_PULLDOWN
#define PIR_ACTIVE_LEVEL  HIGH

// Duman/gaz: panelin/lojik kartın kuru kontağı tipik olarak GND'ye çeker (aktif LOW).
// Kendi donanımınıza göre LOW/HIGH ve PULLUP/PULLDOWN ayarlayın.
#define SMOKE_PINMODE       INPUT_PULLUP
#define SMOKE_ACTIVE_LEVEL  LOW
#define GAS_PINMODE         INPUT_PULLUP
#define GAS_ACTIVE_LEVEL    LOW

// Röle modülü: çoğu modül aktif-LOW'dur. Tetikleme/boşta seviyelerini ayarlayın.
#define RELAY_ACTIVE_LEVEL  HIGH
#define RELAY_IDLE_LEVEL    LOW

// ------------------------------------------------------------------ ZAMANLAMA (ms)
#define FRAME_MS            33     // ~30 FPS çerçeve temposu
#define CORRIDOR_HOLD_MS    20000  // hareket sonrası koridorun açık kalma süresi
#define CORRIDOR_FADE_IN_MS 600    // koridor fade-in süresi
#define CORRIDOR_FADE_OUT_MS 1500  // koridor fade-out süresi
#define ENTRANCE_HOLD_MS    25000  // hareket sonrası girişin açık kalma süresi
#define ENTRANCE_STEP_MS    250    // dikdörtgenler arası sıra gecikmesi
#define RECT_FADE_MS        500    // her dikdörtgenin yumuşak açılma süresi
#define ALARM_BLINK_MS      400    // alarm sırasında kırmızı flaş periyodu
#define SAFETY_DEBOUNCE_MS  300    // duman/gaz girişinin alarm sayılması için stabil kalma süresi
#define ALARM_CLEAR_HOLD_MS 5000   // giriş temizlendikten sonra rölenin bırakılma gecikmesi

// ------------------------------------------------------------------ AĞ / BACKEND
#define WIFI_SSID   "WIFI_ADINIZ"
#define WIFI_PASS   "WIFI_SIFRENIZ"
#define WIFI_RETRY_MS 5000

// FastAPI sunucusu (bu repodaki uygulama). http (LAN) ya da https olabilir.
#define BACKEND_URL "http://192.168.1.50:8000/alerts/sensor"
#define API_KEY     "BACKEND_API_KEY"   // sunucudaki API_KEY ile aynı (x-api-key)

#define ALERT_COOLDOWN_MS     60000  // cihaz tarafı tekrar-gönderim engelleme
#define ALERT_MAX_RETRIES     3
#define ALERT_RETRY_DELAY_MS  1000
