"""README for E-Commerce Price Tracker."""

# E-Commerce Price Tracker

Professional price tracking and analysis pipeline for 650+ e-commerce sites.

## Teknoloji Yığını

- **Language**: Python 3.10+
- **Scraper**: Playwright (JavaScript-based site support)
- **API**: FastAPI
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose

## Proje Yapısı

```
ecommerce-tracker/
├── src/
│   ├── scraper/              # Web scraping logic
│   │   ├── base.py           # Abstract BaseScraper class
│   │   ├── scrapers.py       # Concrete implementations
│   │   └── validators.py     # Data validation
│   ├── api/                  # FastAPI application
│   │   ├── main.py           # App initialization
│   │   ├── routes.py         # API endpoints
│   │   └── models.py         # Pydantic models
│   └── database/             # Database layer
│       ├── connection.py     # PostgreSQL connection
│       ├── models.py         # SQLAlchemy ORM models
│       └── schema.sql        # Database schema
├── data/                     # CSV/JSON outputs
├── logs/                     # Application logs
├── tests/                    # Unit & integration tests
├── config.py                 # Configuration management
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker Compose config
├── Dockerfile                # Docker build config
└── README.md                 # This file
```

## Kurulum (Installation)

### 1. Gereksinimler (Requirements)
- Python 3.10+
- Docker & Docker Compose (isteğe bağlı)
- PostgreSQL (Docker ile veya lokal)

### 2. Virtual Environment Oluşturma

```bash
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
```

### 3. Bağımlılıkları Kurma

```bash
pip install -r requirements.txt
playwright install
```

### 4. Çevre Değişkenlerini Ayarlama

```bash
cp .env.example .env
# Gerekirse .env dosyasını düzenleyin
```

### 5. Veritabanını İnitialize Etme

```bash
python main.py
```

## Kullanım (Usage)

### API Sunucusunu Başlatma

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

API documentation: http://localhost:8000/docs

### Docker ile Çalıştırma

```bash
docker-compose up -d
```

Services:
- API: http://localhost:8000
- Database: localhost:5432
- API Docs: http://localhost:8000/docs

### Testleri Çalıştırma

```bash
pytest -v
pytest --cov=src tests/  # Coverage raporu ile
```

## API Endpoints

### Health Check
```
GET /health
```

### Ürün Yönetimi
```
POST /api/v1/products                      # Yeni ürün oluştur
GET /api/v1/products                       # Tüm ürünleri listele
GET /api/v1/products/{product_id}          # Belirli ürünü getir
GET /api/v1/products/{product_id}/price-history  # Fiyat geçmişi
```

### Scraping
```
POST /api/v1/scraping/batch               # Batch scraping başlat
```

### İstatistikler
```
GET /api/v1/stats                          # Uygulama istatistiği
```

## Özellikler (Features)

✅ **Modüler Yapı**: Scraper, API ve Database bağımsız modüller

✅ **Hata Yönetimi**: Otomatik retry mekanizması ve exponential backoff

✅ **Veri Doğrulama**: Kapsamlı data validation özellikleri

✅ **Ölçeklenebilirlik**: 650+ site için hazır mimari

✅ **Async/Await**: Yüksek concurrency performansı

✅ **Logging**: Detaylı uygulama logları

✅ **API Documentation**: FastAPI Swagger UI

✅ **Docker Support**: Kolay deployment

✅ **Test Coverage**: Unit ve integration testler

## Geliştirme (Development)

### Yeni Scraper Ekleme

```python
from src.scraper import BaseScraper
from src.scraper.validators import DataValidator

class NewSiteScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name="newsite",
            base_url="https://newsite.com"
        )
    
    async def scrape(self, product_url: str) -> dict:
        # Implement scraping logic with Playwright
        pass
    
    async def validate_data(self, data: dict) -> bool:
        return DataValidator.validate_product(data)
```

## Veri Doğruluğu (Data Accuracy)

Sistem şunları sağlar:
- Her ürün verisi otomatik olarak doğrulanır
- Hatalı veriler günlüğe kaydedilir
- Fiyat geçmişi otomatik olarak tutulur
- Duplicate URLs engellenir

## Performance

- Concurrent scraping: Ayarlanabilir (default: 5)
- Request timeout: 30 saniye
- Retry attempts: 3 (exponential backoff)
- Batch processing: Optimization için

## Lisans (License)

MIT

## İletişim (Contact)

Sorular veya öneriler için issues açabilirsiniz.
