import streamlit as st
import pandas as pd
import io
import os
import shutil

# مكتبات توليد الـ PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# مكتبة Google Drive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# 1. الإعدادات الأساسية
FONT_PATH = "Amiri-Bold.ttf"  # اسم ملف الخط العربي (يكون بجانب app.py)
FOLDER_NAME = "Generated_Certificates_Batch"  # اسم المجلد المؤقت محلياً (لو احتجناه)

st.set_page_config(page_title="مولد الشهادات والرفع على درايف", layout="centered")


# دالة الاتصال بجوجل درايف باستخدام Service Account
@st.cache_resource
def authenticate_drive():
    try:
        # تهيئة GoogleAuth واستخدام حساب الخدمة من ملف client_secrets.json
        # ملف client_secrets.json هو ملف الـ Service Account JSON
        gauth = GoogleAuth(
            settings={
                "client_config_backend": "service",
                "service_config": {
                    "client_json_file_path": "client_secrets.json",
                },
                "save_credentials": True,
                "save_credentials_backend": "file",
                "save_credentials_file": "mycreds.txt",
            }
        )

        # مصادقة بحساب الخدمة
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)

        st.sidebar.success("✅ تم الاتصال بجوجل درايف بنجاح بحساب الخدمة!")
        return drive

    except Exception as e:
        st.sidebar.error(
            "❌ خطأ في الاتصال بالدرايف. تأكد من وجود ملف client_secrets.json ومن إعدادات حساب الخدمة."
        )
        st.sidebar.caption(f"الخطأ التقني: {e}")
        return None


# دالة البحث عن مجلد معين في درايف بالاسم
def find_drive_folder(drive, folder_name: str):
    if drive is None:
        return None

    try:
        query = (
            f"title='{folder_name}' and "
            "mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        file_list = drive.ListFile({"q": query}).GetList()
        if file_list:
            return file_list[0]["id"]
        return None
    except Exception:
        return None


# دالة توليد الشهادات والرفع
def generate_and_upload(df, template_path, drive, drive_folder_id, x_pos, y_pos, font_size):
    # 1. إعداد مجلد مؤقت محلياً (لو حابب تستخدمه لاحقاً)
    if os.path.exists(FOLDER_NAME):
        shutil.rmtree(FOLDER_NAME)
    os.makedirs(FOLDER_NAME, exist_ok=True)

    # 2. تسجيل الخط العربي
    pdfmetrics.registerFont(TTFont("ArabicFont", FONT_PATH))

    st.subheader("جاري إنشاء ورفع الشهادات...")
    progress_bar = st.progress(0)
    total = len(df)

    for index, row in df.iterrows():
        # محاولة جلب الاسم من أول عمود
        try:
            name = str(row.iloc[0])
        except Exception:
            name = f"مستخدم-{index + 1}"

        # معالجة النص العربي
        reshaped_text = arabic_reshaper.reshape(name)
        bidi_text = get_display(reshaped_text)

        # إنشاء الـ PDF في الذاكرة
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=landscape(A4))

        # رسم الخلفية (صورة القالب)
        c.drawImage(template_path, 0, 0, width=842, height=595)

        # الكتابة على الشهادة
        c.setFont("ArabicFont", font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x_pos, y_pos, bidi_text)
        c.save()
        packet.seek(0)

        # 3. إعداد بيانات الملف للرفع على جوجل درايف
        file_name = f"شهادة {name}.pdf"
        file_metadata = {
            "title": file_name,
            "parents": [{"id": drive_folder_id}],
            "mimeType": "application/pdf",
        }

        # تنفيذ الرفع
        file = drive.CreateFile(file_metadata)
        file.content = packet
        file.Upload()

        # تحديث شريط التقدم
        progress = (index + 1) / total
        progress_bar.progress(progress)
        st.info(f"تم رفع: {file_name}")

    st.balloons()
    st.success(f"✅ تم الانتهاء! تم إنشاء ورفع {total} شهادة إلى جوجل درايف.")
    shutil.rmtree(FOLDER_NAME, ignore_errors=True)


# ====================================================================
# واجهة المستخدم (UI)
# ====================================================================

st.title("🎓 أداة إنشاء ورفع الشهادات التلقائي")
st.markdown("---")

# المصادقة في الشريط الجانبي أولاً
drive_service = authenticate_drive()

DRIVE_TARGET_FOLDER = st.sidebar.text_input(
    "اسم مجلد درايف الهدف:",
    value="شهادات الكورس",
)

drive_folder_id = (
    find_drive_folder(drive_service, DRIVE_TARGET_FOLDER) if drive_service else None
)

if drive_folder_id:
    st.sidebar.info(
        f"💡 سيتم الرفع إلى المجلد: {DRIVE_TARGET_FOLDER}\n(ID: {drive_folder_id})"
    )
else:
    if drive_service:
        st.sidebar.warning(
            f"⚠️ لم يتم العثور على المجلد '{DRIVE_TARGET_FOLDER}' في درايف.\n"
            "تأكد من وجوده ومشاركته مع بريد حساب الخدمة بصلاحية Editor."
        )

# قسم رفع الملفات
st.header("1. البيانات والقالب")

uploaded_csv = st.file_uploader(
    "ارفع ملف الأسماء (CSV/Excel) - أول عمود هو الاسم",
    type=["csv", "xlsx"],
)

uploaded_template = st.file_uploader(
    "ارفع صورة تصميم الشهادة (JPG/PNG)",
    type=["jpg", "jpeg", "png"],
)

# إعدادات متقدمة لإحداثيات الاسم
with st.expander("2. ضبط إحداثيات الاسم (المكان والحجم)"):
    col1, col2, col3 = st.columns(3)
    with col1:
        font_size = st.number_input("حجم الخط", value=40, min_value=10, max_value=120)
    with col2:
        y_position = st.number_input("الارتفاع (Y Position - من الأسفل)", value=300)
    with col3:
        x_position = st.number_input(
            "المحاذاة الأفقية (X Position - 421 للمنتصف)", value=421
        )

# زر البدء
if st.button("🚀 بدء عملية التوليد والرفع", type="primary"):
    if drive_service is None:
        st.error(
            "يرجى حل مشكلة الاتصال بجوجل درايف أولاً (تأكد من ملف client_secrets.json)."
        )
    elif drive_folder_id is None:
        st.error(
            f"يرجى التأكد من اسم مجلد درايف الهدف '{DRIVE_TARGET_FOLDER}' "
            "ومشاركته مع حساب الخدمة بصلاحية Editor."
        )
    elif uploaded_csv is None or uploaded_template is None:
        st.warning("الرجاء رفع ملف الأسماء وقالب الشهادة أولاً.")
    elif not os.path.exists(FONT_PATH):
        st.error(
            f"ملف الخط العربي ({FONT_PATH}) غير موجود في مجلد التطبيق بجوار app.py."
        )
    else:
        # قراءة ملف الأسماء
        if uploaded_csv.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded_csv)
        else:
            df = pd.read_csv(uploaded_csv)

        # حفظ صورة القالب مؤقتاً
        template_filename = "temp_template.jpg"
        with open(template_filename, "wb") as f:
            f.write(uploaded_template.getbuffer())

        # بدء عملية التوليد والرفع
        try:
            generate_and_upload(
                df=df,
                template_path=template_filename,
                drive=drive_service,
                drive_folder_id=drive_folder_id,
                x_pos=x_position,
                y_pos=y_position,
                font_size=font_size,
            )
        finally:
            # تنظيف الملف المؤقت
            if os.path.exists(template_filename):
                os.remove(template_filename)


