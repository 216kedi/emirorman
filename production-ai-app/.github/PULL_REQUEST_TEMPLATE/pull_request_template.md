## Özet

<!-- Bu PR ne yapıyor ve neden gerekli? 2-3 cümle. -->

## Değişiklik türü

- [ ] Bug fix
- [ ] Yeni özellik
- [ ] Yeniden düzenleme (davranış değişikliği yok)
- [ ] Performans iyileştirmesi
- [ ] Dokümantasyon
- [ ] CI / altyapı

## Etkilenen bileşenler

- [ ] `app/` (API, config, middleware)
- [ ] `components/` (retrieval, reranker)
- [ ] `services/` (LLM, memory, pipeline)
- [ ] `security/` (guard'lar)
- [ ] `evaluation/` (metrikler, judge)
- [ ] `observability/` (metrics, tracing)
- [ ] `agents/`
- [ ] `prompts/`
- [ ] CI/CD / Docker

## Test

<!-- Hangi testleri çalıştırdınız? Yeni test eklediniz mi? -->

```bash
make test
```

- [ ] Birim testler eklendi / güncellendi
- [ ] `make lint` temiz
- [ ] Coverage %60'ın altına düşmüyor

## Kontrol listesi

- [ ] `CHANGELOG.md` → `Unreleased` bölümüne satır eklendi
- [ ] `.env.example` yeni ayar gerektiriyorsa güncellendi
- [ ] Güvenliğe dokunan değişiklik `SECURITY.md` ile tutarlı
- [ ] Yeni `prompts/` şablonu versiyonlu ve `registry.py`'ye kayıtlı
- [ ] Yeni servis / bileşen `CLAUDE.md`'ye eklendi

## Ekran görüntüsü / log çıktısı (opsiyonel)

<!-- İlgili varsa buraya ekleyin. -->
