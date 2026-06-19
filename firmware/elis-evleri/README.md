# Elis Evleri — ESP32 Firmware

Her kata bir ESP32. Tek firmware, iki mod: **giriş katı** ve **üst kat**. PIR
sensörlerle adreslenebilir LED (WS2812) aydınlatması + giriş katında duman/gaz
algılayınca yerel siren (röle) ve apartman sakinlerine WhatsApp bildirimi.

## Pin haritası (ekteki tabloyla birebir)

| Cihaz | Görev | GPIO |
|---|---|---|
| Adreslenebilir LED | Durum göstergesi / aydınlatma (çıkış) | **4** |
| Güvenlik rölesi | Güç/siren kontrolü (çıkış) | **23** |
| 1. PIR | Giriş — dikdörtgenler (giriş) | **25** |
| 2. PIR | Koridor ucu A (giriş) | **26** |
| 3. PIR | Koridor ucu B (giriş) | **27** |
| Gaz sensörü | Lojik kart sinyali (giriş) | **19** |
| Duman dedektörü | Yangın röle sinyali (giriş) | **18** |

## Davranış

**Giriş katı (`MODE_GROUND`)**
- **PIR1 (25)** hareket algılayınca → girişteki **iç içe dikdörtgenler sırayla** yanar
  (her biri yumuşak fade ile). Hareket bitip bekleme süresi dolunca ters sırayla söner.
- **PIR2 (26)** veya **PIR3 (27)** (koridorun iki ucu) → koridor **fade in**; ikisi de
  bir süre pasif kalınca **fade out**.
- **Duman (18)** veya **gaz (19)** alarmı → güvenlik rölesi (23) **siren ON** + tüm LED'ler
  **kırmızı flaş** + backend'e POST (→ WhatsApp). Giriş temizlenince röle bırakılır.

**Üst kat (`MODE_UPPER`)**
- Koridorun iki ucundaki **2 PIR (26/27)** → koridor **fade in/out**. Duman/gaz/röle yok.

> Güvenlik notu: alarmda **röle ve LED yereldir, WiFi'a bağlı değildir**. Konvansiyonel
> yangın paneli kendi sirenini zaten çalar; ESP32 ek bildirim/otomasyon katmanıdır.

## Yapılandırma

Tüm ayarlar **`src/config.h`** içinde. Her kat için düzenleyin:
- `FLOOR_MODE` (`MODE_GROUND` / `MODE_UPPER`), `FLOOR_NUMBER`, `DEVICE_ID`
- `NUM_LEDS` ve bölge aralıkları: `CORRIDOR_START/COUNT`, `RECT_RANGES` (dikdörtgenler)
  — *bina ölçülünce gerçek LED sayılarıyla güncelleyin.*
- Giriş seviyeleri: PIR `HIGH`/pulldown; duman/gaz `LOW`/pullup (panel kuru kontağı GND'ye
  çekiyorsa). Röle modülünüz aktif-LOW ise `RELAY_ACTIVE_LEVEL`/`IDLE_LEVEL` değiştirin.
- Ağ: `WIFI_SSID`, `WIFI_PASS`, `BACKEND_URL`, `API_KEY` (sunucudaki `API_KEY` ile aynı).

## Derleme ve yükleme

**PlatformIO (önerilen)**
```bash
cd firmware/elis-evleri
pio run                 # derle
pio run -t upload       # ESP32'ye yükle
pio device monitor      # seri monitör (115200)
```

**Arduino IDE (alternatif)**
1. `src/main.cpp` → `elis_evleri/elis_evleri.ino` olarak kopyalayın, `config.h`'yi aynı
   klasöre koyun.
2. Kart: "ESP32 Dev Module". Library Manager'dan **FastLED** kurun.
3. Derleyip yükleyin.

## Backend (WhatsApp) tarafı

ESP32, alarmı bu repodaki FastAPI sunucusuna (`production-ai-app`) gönderir; sunucu Meta
WhatsApp Cloud API ile **tüm sakinlere** mesaj atar.

ESP32 → backend isteği:
```
POST {BACKEND_URL}        Header: x-api-key: {API_KEY}
{"device_id":"elis-giris-1","floor":"0","sensor":"gas","state":"alarm"}
```

### Meta WhatsApp Cloud API kurulumu (bir kez)
1. Meta for Developers → uygulama + **WhatsApp Business Account**; gönderen numara ekle →
   **Phone Number ID**.
2. **Kalıcı (System User) access token** üret.
3. **Şablon** oluştur/onaylat — ad `elis_alarm`, dil `tr`, gövde:
   `⚠️ {{1}} - {{2}}. katta {{3}} alarmı! Saat {{4}}. Lütfen binayı kontrol edin.`
   (sıra: bina, kat, sensör, saat).
4. Sunucu `.env`: `API_KEY`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`,
   `WHATSAPP_TEMPLATE_NAME`, `WHATSAPP_TEMPLATE_LANG`, `WHATSAPP_RECIPIENTS` (virgülle
   ayrık `+90...` numaralar), `BUILDING_NAME`.

Sunucu çalıştırma ve uçtan uca test için `production-ai-app/` README'ye ve
`/alerts/sensor` endpoint'ine bakın.
