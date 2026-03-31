# OmniNexus — Kurulum Kılavuzu

## Gereksinimler
- Python 3.10+
- MySQL (GoDaddy cPanel)
- NewsAPI key (newsapi.org — ücretsiz)

---

## 1. API Keyleri Al

### NewsAPI (Ücretsiz)
1. https://newsapi.org adresine git
2. "Get API Key" butonuna tıkla
3. Ücretsiz hesap oluştur (günde 100 istek)
4. API key'ini kopyala

### Google Translate (Opsiyonel)
- https://console.cloud.google.com üzerinden alınır
- Ücretsiz kota: 500.000 karakter/ay
- Yoksa LibreTranslate otomatik devreye girer

---

## 2. GoDaddy cPanel MySQL Kurulumu

1. cPanel → **MySQL Databases** aç
2. Yeni veritabanı oluştur: `omninexus`
3. Yeni kullanıcı oluştur, güçlü şifre ver
4. Kullanıcıyı veritabanına ekle — **All Privileges** ver
5. Host genellikle `localhost`

---

## 3. Ortam Değişkenleri

cPanel → **Setup Python App** bölümünde Environment Variables ekle:

```
SECRET_KEY          = guclu-rastgele-bir-key-yaz
MYSQL_HOST          = localhost
MYSQL_USER          = cpanel_kullanici_adi
MYSQL_PASSWORD      = mysql_sifren
MYSQL_DB            = omninexus
NEWS_API_KEY        = newsapi_key_buraya
GOOGLE_TRANSLATE_KEY = (opsiyonel)
```

---

## 4. GoDaddy cPanel'e Yükleme

1. cPanel → **File Manager** → `public_html/omninexus` klasörü oluştur
2. Tüm dosyaları yükle
3. cPanel → **Setup Python App**:
   - Python version: 3.11
   - Application root: `public_html/omninexus`
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
4. **Install Dependencies** tıkla (requirements.txt otomatik okunur)
5. Restart App

---

## 5. Domain Bağlantısı

cPanel → **Domains** → `omninexus.com` → Application root olarak `/omninexus` göster

---

## 6. SSL Aktif Et (PWA için zorunlu)

cPanel → **SSL/TLS** → **AutoSSL** → Let's Encrypt ücretsiz SSL

---

## Yerel Test (Geliştirme)

```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000 aç
```

---

## Proje Yapısı

```
omninexus/
├── app.py              # Ana Flask uygulaması
├── config.py           # Ayarlar (API keys, DB)
├── models.py           # Veritabanı modelleri
├── passenger_wsgi.py   # GoDaddy WSGI dosyası
├── requirements.txt    # Python paketleri
├── routes/
│   ├── main.py         # Ana sayfa + translate API
│   ├── auth.py         # Login / Register / Logout
│   ├── news.py         # NewsAPI entegrasyonu
│   └── comments.py     # Yorum sistemi
├── templates/
│   └── index.html      # Ana HTML şablonu
└── static/
    ├── css/main.css    # Tüm stiller
    ├── js/main.js      # Frontend JavaScript
    ├── manifest.json   # PWA manifest
    ├── sw.js           # Service Worker
    └── icons/          # Uygulama ikonları
```
