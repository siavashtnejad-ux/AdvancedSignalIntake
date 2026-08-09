# Ethical Horizon Intelligence v3

نسخه Standalone سامانه هوشمندی سیگنال‌های زیست‌پزشکی.

## قابلیت‌های این نسخه

- رابط فارسی و RTL
- Backend واقعی با FastAPI
- SQLite محلی و مستقل از Supabase
- اتصال مستقیم به:
  - PubMed / MEDLINE
  - ClinicalTrials.gov API v2
  - OpenAlex
  - Crossref
- حذف رکوردهای تکراری با DOI / عنوان
- ذخیره تاریخچه Scan و Evidence
- Signal Intelligence Engine
- تحلیل پنج حوزه اخلاقی
- برآورد بلوغ فناوری
- تحلیل ارتباط با ایران
- تحلیل روند زمانی از نمونه شواهد بازیابی‌شده
- Clinical Activity Score
- Novelty Score
- Signal Score
- خروجی JSON / CSV / PDF
- تست‌های پایه

---

## نصب

Python 3.11+ توصیه می‌شود.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## تنظیم APIها

فایل `.env.example` فقط نمونه است. متغیرها را در محیط سیستم قرار دهید.

Linux/macOS:

```bash
export NCBI_EMAIL="you@example.org"
export CROSSREF_MAILTO="you@example.org"
export OPENALEX_API_KEY="YOUR_OPENALEX_KEY"
```

Windows PowerShell:

```powershell
$env:NCBI_EMAIL="you@example.org"
$env:CROSSREF_MAILTO="you@example.org"
$env:OPENALEX_API_KEY="YOUR_OPENALEX_KEY"
```

### نکته OpenAlex

در سال 2026 استفاده عادی از API OpenAlex نیازمند API key است. اگر Key تنظیم نشده باشد، برنامه خراب نمی‌شود؛ OpenAlex را Skip می‌کند و Warning در Dashboard نمایش می‌دهد.

---

## اجرا

```bash
python run.py
```

سپس:

```text
http://127.0.0.1:8080
```

Swagger API:

```text
http://127.0.0.1:8080/docs
```

---

## API داخلی

### Health

```http
GET /api/health
```

### منابع

```http
GET /api/sources
```

### اجرای Scan

```http
POST /api/scan
Content-Type: application/json
```

نمونه:

```json
{
  "query": "AI assisted cancer diagnosis",
  "sources": ["pubmed","clinicaltrials","openalex","crossref"],
  "max_results": 25,
  "from_year": 2022,
  "to_year": 2026,
  "iran_focus": false
}
```

### تاریخچه

```http
GET /api/scans
GET /api/scans/1
```

### سیگنال‌ها

```http
GET /api/signals
```

### Export

```http
GET /api/export/1.json
GET /api/export/1.csv
GET /api/export/1.pdf
```

---

## SQLite

Database در اولین اجرا خودکار ساخته می‌شود:

```text
data/ethical_horizon.db
```

جداول:

- `sources`
- `scans`
- `evidence`
- `scan_evidence`
- `signals`

این لایه عمداً مستقل نوشته شده تا بعداً بتوان آن را با Adapter مربوط به Supabase/PostgreSQL جایگزین کرد.

---

## مدل Signal Score

نسخه فعلی از یک heuristic شفاف و قابل تغییر استفاده می‌کند:

```text
Trend / Evidence Growth     25%
Clinical Activity           25%
Ethical Complexity          20%
Iran Relevance              15%
Technology Novelty          15%
```

این امتیاز **یک معیار پژوهشی اعتبارسنجی‌شده نیست**. هدف آن اولویت‌بندی اکتشافی Candidate Signals است. قبل از استفاده به‌عنوان خروجی رسمی مطالعه، وزن‌ها و thresholds باید با تیم پژوهش و روش اعتبارسنجی مشخص شوند.

---

## تحلیل اخلاق

پنج حوزه زیر در موتور Rule-Based لحاظ شده‌اند:

1. اخلاق پژوهش
2. اخلاق بالینی
3. اخلاق فناوری‌های نوین و داده
4. عدالت و حکمرانی سلامت
5. اخلاق سازمانی در نظام سلامت

---

## محدودیت روند

Trend Score فعلی از توزیع سال انتشار **نمونه رکوردهای بازیابی‌شده** محاسبه می‌شود؛ نه از شمارش جامع سالانه تمام رکوردهای یک پایگاه. این موضوع در طراحی عمداً شفاف است.

برای نسخه پژوهشی بعدی می‌توان trend endpoint مستقل با شمارش سالانه کامل در PubMed/OpenAlex اضافه کرد.

---

## تست

```bash
pytest -q
```

یا بدون pytest:

```bash
python -m compileall backend
```

---

## مهاجرت آینده به Supabase

در نسخه فعلی هیچ اتصال Supabase وجود ندارد.

برای مهاجرت بعدی، کافی است Interface عملیاتی `Database` در `backend/database.py` با یک Adapter PostgreSQL/Supabase جایگزین شود. Connectorها، Analysis Engine، Frontend و API contract نیازی به بازنویسی اساسی ندارند.

## به‌روزرسانی رابط کاربری

در این نسخه:
- Search Bar به Hero بالای صفحه منتقل شده است.
- اندازه فونت‌ها و عناصر خواندنی افزایش یافته است.
- تصویر `frontend/header-hero.webp` به‌صورت محلی در پروژه قرار دارد و برای هدر استفاده می‌شود.

## GitHub Pages

این Repository شامل دو لایه است:

- `frontend/` + `backend/`: برنامه Full-stack با FastAPI و SQLite
- `docs/`: نسخه استاتیک مخصوص GitHub Pages

Workflow موجود در `.github/workflows/pages.yml` پوشه `docs/` را روی GitHub Pages منتشر می‌کند.

توجه: GitHub Pages امکان اجرای Python/FastAPI یا SQLite server-side را ندارد؛ بنابراین نسخه Pages برای نمایش عمومی UI است. جستجوی واقعی، ذخیره‌سازی SQLite، تاریخچه و Export در نسخه Full-stack اجرا می‌شوند.
