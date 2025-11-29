# 🔧 دليل حل المشاكل

## ❌ خطأ: `SSL: WRONG_VERSION_NUMBER`

### السبب
هذا الخطأ يحدث عندما يفشل الاتصال بـ Google Drive API بسبب مشكلة في SSL/TLS.

### الأسباب المحتملة:
1. **مشكلة في الإنترنت** - اتصال ضعيف أو منقطع
2. **Proxy/Firewall** - برنامج حماية أو شبكة مؤسسية تحجب الوصول
3. **Token منتهي الصلاحية** - الـ OAuth token قديم أو تالف
4. **VPN/Antivirus** - برامج تتداخل مع اتصال SSL

---

## 🔨 الحلول

### ✅ الحل 1: إعادة المصادقة (الأسهل)

1. في Sidebar، اضغط على زر **"🔄 إعادة المصادقة"**
2. سيتم حذف `token.json` تلقائياً
3. أعد تحميل الصفحة (`F5` أو `Ctrl+R`)
4. سجّل دخول من جديد

**أو يدوياً:**
```bash
# احذف ملف token.json
del token.json  # في Windows
rm token.json   # في Linux/Mac

# أعد تشغيل التطبيق
streamlit run app.py
```

---

### ✅ الحل 2: تحقق من الإنترنت

1. تأكد من اتصالك بالإنترنت:
   ```bash
   ping google.com
   ```

2. جرّب فتح [https://drive.google.com](https://drive.google.com) في المتصفح
3. إذا لم يعمل، تحقق من إعدادات الشبكة

---

### ✅ الحل 3: تعطيل VPN/Antivirus مؤقتاً

بعض برامج VPN أو Antivirus تتداخل مع اتصالات SSL:

1. **عطّل VPN** إذا كنت تستخدم واحداً
2. **عطّل Antivirus مؤقتاً** (أو أضف Python/Streamlit للاستثناءات)
3. جرّب التطبيق مرة أخرى

**برامج معروفة بالتداخل:**
- Kaspersky (SSL Scanning)
- Avast/AVG (HTTPS Scanning)
- Norton (SSL Protection)
- ZScaler

---

### ✅ الحل 4: استخدام Proxy (إذا كنت في شبكة مؤسسية)

إذا كنت خلف Proxy في الشركة/الجامعة:

1. **اضبط متغيرات البيئة:**

**Windows PowerShell:**
```powershell
$env:HTTP_PROXY="http://proxy-address:port"
$env:HTTPS_PROXY="http://proxy-address:port"
streamlit run app.py
```

**Windows CMD:**
```cmd
set HTTP_PROXY=http://proxy-address:port
set HTTPS_PROXY=http://proxy-address:port
streamlit run app.py
```

**Linux/Mac:**
```bash
export HTTP_PROXY="http://proxy-address:port"
export HTTPS_PROXY="http://proxy-address:port"
streamlit run app.py
```

2. استبدل `proxy-address:port` بعنوان الـ Proxy الخاص بك

---

### ✅ الحل 5: تحديث Certificates

في بعض الحالات، SSL certificates قديمة:

**Windows:**
```bash
python -m pip install --upgrade certifi
```

**Linux/Mac:**
```bash
pip install --upgrade certifi
```

ثم أعد تشغيل التطبيق.

---

### ✅ الحل 6: إعادة إنشاء OAuth Credentials

إذا استمرت المشكلة:

1. احذف الملفات:
   - `token.json`
   - `oauth_credentials.json`

2. أعد إنشاء OAuth Client ID من [Google Cloud Console](https://console.cloud.google.com/)

3. نزّل الملف الجديد وسمّه `oauth_credentials.json`

4. ضعه في مجلد التطبيق

5. شغّل التطبيق:
   ```bash
   streamlit run app.py
   ```

---

## 🔍 تحديد المشكلة بدقة

### اختبار الاتصال بـ Google APIs:

```python
# ملف اختبار بسيط: test_connection.py
import requests

try:
    response = requests.get('https://www.googleapis.com', timeout=5)
    print(f"✅ الاتصال ناجح: {response.status_code}")
except Exception as e:
    print(f"❌ فشل الاتصال: {e}")
```

شغّله:
```bash
python test_connection.py
```

---

## 🆘 مشاكل أخرى شائعة

### مشكلة: "Access blocked: Certificate Generator has not completed verification"

**الحل:**
1. افتح [Google Cloud Console](https://console.cloud.google.com/)
2. اذهب إلى **APIs & Services** → **OAuth consent screen**
3. اضغط **ADD USERS** تحت "Test users"
4. أضف بريدك الإلكتروني
5. احفظ وأعد المحاولة

---

### مشكلة: "ملف الخط العربي غير موجود"

**الحل:**
تأكد من وجود `Amiri-Bold.ttf` في نفس المجلد مع `app.py`:
```
cert_gen/
├── app.py
├── Amiri-Bold.ttf  ← هنا
├── requirements.txt
└── oauth_credentials.json
```

إذا لم يكن موجوداً، نزّله من:
- [Google Fonts - Amiri](https://fonts.google.com/specimen/Amiri)

---

### مشكلة: "ImportError: Missing optional dependency"

**الحل:**
```bash
pip install openpyxl
```

أو أعد تثبيت كل المكتبات:
```bash
pip install -r requirements.txt
```

---

## 📞 الحصول على مساعدة إضافية

إذا استمرت المشكلة:

1. **تحقق من الـ logs** في Terminal:
   - ابحث عن رسائل الخطأ الكاملة
   - انسخها للمرجعية

2. **جرّب في بيئة نظيفة:**
   ```bash
   # إنشاء virtual environment جديد
   python -m venv test_env
   test_env\Scripts\activate  # Windows
   pip install -r requirements.txt
   streamlit run app.py
   ```

3. **راجع الوثائق:**
   - `README.md` - الدليل الشامل
   - `QUICKSTART.md` - البدء السريع
   - `SETUP_INSTRUCTIONS.md` - إعداد OAuth

---

## ✅ Checklist للتأكد

قبل التواصل للدعم، تأكد من:

- [ ] الإنترنت يعمل بشكل صحيح
- [ ] ملف `oauth_credentials.json` موجود وصحيح
- [ ] جربت حذف `token.json` وإعادة المصادقة
- [ ] VPN/Antivirus معطّل مؤقتاً
- [ ] جربت في بيئة Python نظيفة
- [ ] Python 3.8 - 3.11 (ليس 3.12+ أو 3.7-)
- [ ] كل المكتبات من `requirements.txt` مثبتة

---

**نصيحة:** في 90% من الحالات، حذف `token.json` وإعادة المصادقة يحل المشكلة! 🎯

