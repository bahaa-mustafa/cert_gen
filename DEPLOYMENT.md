# 🚀 دليل النشر على Streamlit Cloud

هذا الدليل يشرح كيفية نشر التطبيق على Streamlit Cloud.

---

## 📋 المتطلبات

1. ✅ حساب على [GitHub](https://github.com)
2. ✅ حساب على [Streamlit Cloud](https://streamlit.io/cloud)
3. ✅ حساب على [Google Cloud Console](https://console.cloud.google.com/)
4. ✅ OAuth Client ID من Google Cloud Console

---

## 🔧 الخطوة 1: إعداد GitHub Repository

### 1.1 رفع الكود على GitHub

```bash
# إذا لم يكن لديك repository بعد
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**ملاحظة مهمة:** تأكد من رفع ملف `Amiri-Bold.ttf` على GitHub (لا يجب أن يكون في `.gitignore`).

---

## 🔑 الخطوة 2: إعداد OAuth Credentials

### 2.1 إنشاء OAuth Client ID (Web Application)

1. افتح [Google Cloud Console](https://console.cloud.google.com/)
2. اذهب إلى **APIs & Services** → **Credentials**
3. اضغط **+ CREATE CREDENTIALS** → **OAuth client ID**
4. اختر **Web application** (ليس Desktop app!)
5. أضف **Authorized redirect URIs**:
   ```
   https://YOUR_APP_NAME.streamlit.app/
   ```
   (ستحصل على الرابط بعد النشر على Streamlit Cloud)
6. احفظ **Client ID** و **Client Secret**

### 2.2 تحويل OAuth Credentials إلى JSON

أنشئ ملف JSON بهذا الشكل:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "YOUR_PROJECT_ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

**أو** استخدم ملف `oauth_credentials.json` الموجود لديك (لكن تأكد من إضافة redirect URI للـ Cloud).

---

## ☁️ الخطوة 3: إعداد Streamlit Cloud

### 3.1 ربط GitHub مع Streamlit Cloud

1. افتح [Streamlit Cloud](https://share.streamlit.io/)
2. اضغط **Sign in** وسجّل دخول بحساب GitHub
3. اضغط **New app**
4. اختر:
   - **Repository**: repository الخاص بك
   - **Branch**: `main` (أو `master`)
   - **Main file path**: `app.py`

### 3.2 إضافة Streamlit Secrets

1. في صفحة التطبيق، اضغط **☰** (القائمة) → **Settings**
2. اذهب إلى **Secrets**
3. أضف المحتوى التالي:

```toml
[oauth_credentials]
installed = """
{
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "project_id": "YOUR_PROJECT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uris": ["http://localhost"]
}
"""
```

**استبدل:**
- `YOUR_CLIENT_ID` → Client ID من Google Cloud Console
- `YOUR_PROJECT_ID` → Project ID من Google Cloud Console
- `YOUR_CLIENT_SECRET` → Client Secret من Google Cloud Console

**⚠️ ملاحظات مهمة عند إضافة Secrets:**
- ✅ انسخ المحتوى **بالضبط كما هو** بما في ذلك `"""` و `[oauth_credentials]`
- ✅ تأكد من استبدال `YOUR_CLIENT_ID` و `YOUR_PROJECT_ID` و `YOUR_CLIENT_SECRET` ببياناتك الفعلية
- ✅ احتفظ بـ `installed` و `"""` كما هما - هذه جزء من الصيغة
- ✅ JSON يجب أن يكون **داخل** علامات التنصيص الثلاثية `"""`
- ⚠️ **لا تنسخ** محتوى `oauth_credentials.json` مباشرة - استخدم الصيغة أعلاه
- 🔄 بعد الحفظ، أعد تشغيل التطبيق من **Manage app** → **Reboot**

### 3.3 بدء النشر

1. اضغط **Save**
2. اضغط **Deploy** أو انتظر النشر التلقائي
3. بعد النشر، ستحصل على رابط مثل: `https://YOUR_APP_NAME.streamlit.app/`

### 3.4 التحقق من نجاح الإعداد

بعد النشر، افتح التطبيق وتحقق من:
- ✅ يظهر في الـ sidebar: "✅ متصل بالدرايف" أو خطوات المصادقة
- ❌ إذا ظهر "❌ ملف OAuth غير موجود" → راجع قسم **حل المشاكل** أدناه
- ⚠️ إذا ظهر "⚠️ خطأ في قراءة Secrets" → تحقق من صيغة JSON في Secrets

---

## 🔄 الخطوة 4: تحديث Redirect URI

بعد الحصول على رابط التطبيق:

1. اذهب إلى [Google Cloud Console](https://console.cloud.google.com/)
2. **APIs & Services** → **Credentials**
3. اضغط على OAuth Client ID الخاص بك
4. أضف **Authorized redirect URI**:
   ```
   https://YOUR_APP_NAME.streamlit.app/
   ```
5. احفظ التغييرات

---

## ⚠️ ملاحظات مهمة

### 1. ملف الخط العربي
- ✅ تأكد من رفع `Amiri-Bold.ttf` على GitHub
- ✅ الملف يجب أن يكون في نفس المجلد مع `app.py`

### 2. OAuth Flow على Streamlit Cloud
- ⚠️ **مشكلة:** `run_local_server` لا يعمل على Streamlit Cloud
- 💡 **الحل الحالي:** المستخدم يحتاج لتسجيل الدخول محلياً أولاً لإنشاء token
- 🔄 **بديل:** يمكن استخدام Service Account (لكن يحتاج تعديلات)

### 3. Token Storage
- Token يُحفظ في Streamlit Session State
- قد تحتاج لإعادة تسجيل الدخول في كل جلسة جديدة

---

## 🧪 اختبار التطبيق

بعد النشر:

1. افتح رابط التطبيق: `https://YOUR_APP_NAME.streamlit.app/`
2. جرّب رفع ملف CSV/Excel و PDF
3. تأكد من عمل المصادقة مع Google Drive
4. تأكد من رفع الشهادات بنجاح

---

## 🔧 حل المشاكل

### المشكلة: "ملف OAuth غير موجود"
**الحل:** تأكد من إضافة Secrets في Streamlit Cloud Settings

**خطوات التحقق:**
1. افتح تطبيقك على Streamlit Cloud
2. اضغط **☰** → **Settings** → **Secrets**
3. تأكد من وجود المحتوى بالصيغة الصحيحة (مع `[oauth_credentials]` و `installed = """`)
4. اضغط **Save**
5. من **Manage app** → اضغط **Reboot** لإعادة تشغيل التطبيق
6. إذا استمرت المشكلة، راجع لوجود رسالة "⚠️ خطأ في قراءة Secrets" في الـ sidebar

**سبب شائع:** نسخ محتوى `oauth_credentials.json` مباشرة بدلاً من استخدام صيغة TOML الصحيحة

### المشكلة: "⚠️ خطأ في قراءة Secrets"
**الحل:** 
1. تأكد من صيغة JSON داخل `"""` صحيحة (بدون فواصل زائدة)
2. تأكد من وجود جميع الحقول المطلوبة
3. جرب نسخ الصيغة من القسم 3.2 أعلاه مباشرة

### المشكلة: "SSL: WRONG_VERSION_NUMBER"
**الحل:** راجع ملف `TROUBLESHOOTING.md`

### المشكلة: "Access blocked"
**الحل:** 
1. أضف حسابك كـ "Test user" في OAuth Consent Screen
2. راجع `SETUP_INSTRUCTIONS.md`

### المشكلة: Token لا يُحفظ
**الحل:** هذا طبيعي على Streamlit Cloud - ستحتاج لإعادة تسجيل الدخول في كل جلسة

---

## 📚 ملفات مرجعية

- `README.md` - الدليل الشامل
- `QUICKSTART.md` - البدء السريع
- `SETUP_INSTRUCTIONS.md` - إعداد OAuth
- `TROUBLESHOOTING.md` - حل المشاكل

---

## ✅ Checklist قبل النشر

- [ ] الكود مرفوع على GitHub
- [ ] ملف `Amiri-Bold.ttf` موجود في Repository
- [ ] OAuth Client ID من نوع "Web Application"
- [ ] Streamlit Secrets مُعدّ بشكل صحيح
- [ ] Redirect URI مضاف في Google Cloud Console
- [ ] التطبيق يعمل محلياً بدون أخطاء

---

**بعد إكمال جميع الخطوات، التطبيق سيكون جاهزاً على Streamlit Cloud! 🎉**

