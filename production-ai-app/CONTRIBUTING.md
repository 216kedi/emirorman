# Katkı Rehberi

Katkınız için teşekkürler. Aşağıdaki adımları izleyin.

## Hızlı başlangıç

```bash
git clone https://github.com/your-org/production-ai-app
cd production-ai-app
cp .env.example .env          # API key'leri doldurun
make dev                       # bağımlılıkları kur + pre-commit'i etkinleştir
docker compose up -d qdrant redis
make migrate && make seed
make api                       # http://localhost:8000/docs
```

## Geliştirme akışı

1. `main` üzerinden yeni bir dal açın: `git checkout -b feat/my-feature`
2. Değişikliklerinizi yapın — her yeni modül için `tests/` altında test ekleyin
3. `make lint && make test` geçmeli
4. PR açın; CI otomatik çalışır

## Kod standartları

- `claude/rules/code-style.md` kuralları geçerlidir
- Tüm I/O async olmalı; sync `requests` servis katmanında kullanılmaz
- LLM çağrıları `services/llm/base.py` üzerinden gider; `anthropic`/`openai` modüllerini doğrudan import etmeyin
- Yeni prompt → `prompts/templates.py`'ye versiyonlu olarak ekleyin, `registry.py`'ye kaydedin
- Güvenlik guard'larını hiçbir koşulda bypass etmeyin
- Fonksiyon başına tek sorumluluk; docstring değil, açıklayıcı isimler

## Test yazımı

- `pytest-asyncio` ile async testler: `asyncio_mode = "auto"` zaten ayarlı
- LLM ve vector DB çağrıları `respx` / `pytest-httpx` ile mock'lanmalı
- Redis gerektiren testler `fakeredis` veya CI servisini kullanmalı
- `make test-cov` — coverage %60 altına düşmemeli

## PR kontrolü

- [ ] `make lint` temiz
- [ ] `make test` geçiyor
- [ ] Yeni bileşen için test var
- [ ] `CHANGELOG.md` güncellemesi `Unreleased` bölümüne eklendi
- [ ] `.env.example` yeni ayar gerektiriyorsa güncellendi
- [ ] Güvenliğe dokunan değişiklik `SECURITY.md` tehdit modeli ile tutarlı

## Sürüm yönetimi

[Semantic Versioning](https://semver.org/) kullanıyoruz.
Etiket push'u `release.yml` workflow'unu tetikler ve otomatik release notu üretir.

```bash
git tag v0.3.0
git push origin v0.3.0
```

## Güvenlik açığı bildirimi

`SECURITY.md`'ye bakın.
