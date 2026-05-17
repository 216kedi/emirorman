# Security Policy

## Desteklenen sürümler

| Sürüm | Destek         |
| ----- | -------------- |
| 0.x   | Aktif          |

## Güvenlik açığı bildirme

Lütfen güvenlik açıklarını genel GitHub issue'ları üzerinden bildirmeyin.

Bunun yerine [GitHub Private Security Advisories](https://github.com/your-org/production-ai-app/security/advisories/new) üzerinden bildirin ya da `security@your-org.example` adresine e-posta gönderin.

24 saat içinde yanıt vermeye çalışıyoruz. Kritik açıklar için 72 saat içinde düzeltme hedefliyoruz.

## Tehdit Modeli

### Güven sınırları

| Kaynak           | Güven düzeyi | Açıklama                                      |
| ---------------- | ------------ | --------------------------------------------- |
| API istemcileri  | Düşük        | Tüm input'lar input_guard'dan geçirilir       |
| LLM çıktıları    | Orta         | output_filter ile doğrulanır                  |
| Veritabanı       | Yüksek       | Ağ politikası ile korunur                     |
| Üçüncü taraf LLM | Orta         | API key'ler env'den yüklenir, loglanmaz       |

### Kontroller

| Risk                   | Kontrol                                               |
| ---------------------- | ----------------------------------------------------- |
| Prompt injection       | `security/input_guard.py` regex + pattern eşleştirme |
| PII sızıntısı          | `security/content_filter.py` redaction               |
| Halüsinasyon sızıntısı | `security/output_filter.py` grounding kontrolü       |
| Kaba kuvvet / DDoS     | slowapi rate limiting (60 req/dk varsayılan)          |
| Yetkisiz erişim        | API key auth (`x-api-key` header)                    |
| Dependency CVE         | `pip-audit` CI job'u                                 |
| Gizli veri sızıntısı   | detect-secrets pre-commit hook                        |
| Container escape       | Non-root kullanıcı, minimal base image               |
| SBOM                   | Anchore CI job'u (main branch)                       |

### Kapsam dışı

- Fiziksel güvenlik
- Sosyal mühendislik
- Ağ altyapısı güvenliği (bulut sağlayıcı sorumluluğu)
