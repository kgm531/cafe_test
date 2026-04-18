# ☕ BREW & BOND - نظام ولاء الكافيه

نظام ولاء متكامل لكافيه مع بطاقة رقمية وQR Code وربط مع Apple Pay / Samsung Pay.

## 🏗️ هيكل المشروع

```
cafe-loyalty/
├── app.py                  # Flask Backend (Python)
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # HTML Template
└── static/
    ├── css/
    │   └── style.css       # Stylesheet
    └── js/
        └── app.js          # Frontend JavaScript
```

## 🚀 التشغيل

### 1. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 2. تشغيل السيرفر
```bash
python app.py
```

### 3. فتح المتصفح
```
http://localhost:5000
```

## ✨ المميزات

### نظام الولاء
- كل عميل يحصل على **رقم عضوية فريد** (مثل CF-A3K7NP)
- بعد شراء **7 مشروبات** يحصل على الثامن **مجاناً**
- بطاقة ختم رقمية تتبع التقدم
- احتفال بصري (confetti) عند الحصول على مشروب مجاني

### البطاقة الرقمية
- **QR Code** فريد لكل عميل يتم توليده من الباك إند
- أزرار إضافة البطاقة إلى **Apple Pay** و **Samsung Pay**
- شريط تقدم متحرك
- تحميل بطاقة المحفظة كصورة PNG

### قائمة المشروبات
- 14 مشروب في 3 فئات (ساخن / بارد / مميز)
- فلترة حسب الفئة
- سلة مشتريات ذكية

### لوحة الإدارة
- البحث عن العملاء بالرقم
- إضافة أختام يدوياً (API)
- عرض جميع العملاء (API)

## 🔌 API Endpoints

| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/api/drinks` | قائمة المشروبات |
| POST | `/api/register` | تسجيل عميل جديد |
| GET | `/api/customer/<id>` | بيانات عميل |
| POST | `/api/order` | تسجيل طلب جديد |
| GET | `/api/qr/<id>` | تحميل QR Code |
| GET | `/api/wallet/<id>` | تحميل بطاقة المحفظة |
| GET | `/api/admin/customers` | جميع العملاء |
| POST | `/api/admin/add-stamp` | إضافة ختم يدوي |

## 🔧 للإنتاج

### قاعدة بيانات
استبدل `customers_db` و `orders_db` بقاعدة بيانات حقيقية مثل:
- **SQLite** (بسيط)
- **PostgreSQL** (موصى به)
- **MongoDB** (مرن)

### Apple Wallet
لربط Apple Wallet فعلياً:
1. احصل على شهادة Apple Developer
2. استخدم مكتبة `wallet-py` لتوليد ملفات `.pkpass`
3. أضف endpoint لتوليد الملفات

### Samsung Pay
لربط Samsung Pay فعلياً:
1. سجل في Samsung Wallet Partner Portal
2. استخدم Samsung Wallet API
3. أضف endpoint لتوليد بطاقات Samsung

### الاستضافة
```bash
# باستخدام Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
