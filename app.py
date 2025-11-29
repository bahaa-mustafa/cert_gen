import streamlit as st
import pandas as pd
import io
import os
import shutil
import json


# مكتبات توليد الـ PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# مكتبة pypdf للتعامل مع ملفات PDF
from pypdf import PdfReader, PdfWriter

# مكتبات Google Drive API
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. الإعدادات الأساسية
FONT_PATH = "Amiri-Bold.ttf"  # اسم ملف الخط العربي (يكون بجانب app.py)
FOLDER_NAME = "Generated_Certificates_Batch"  # اسم المجلد المؤقت محلياً (لو احتجناه)

st.set_page_config(
    page_title="مولد الشهادات",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)


# دالة قراءة Service Account credentials من Streamlit Secrets أو ملف محلي
def get_service_account_credentials():
    """
    قراءة Service Account credentials من Streamlit Secrets (للنشر) أو ملف محلي (للتطوير)
    """
    # محاولة القراءة من Streamlit Secrets (للنشر على Cloud)
    try:
        if 'service_account' in st.secrets:
            # تحويل Streamlit secrets إلى dict عادي
            return dict(st.secrets['service_account'])
    except Exception as e:
        st.sidebar.warning(f"⚠️ خطأ في قراءة Secrets: {str(e)}")
    
    # إذا لم توجد secrets، اقرأ من ملف محلي (للتطوير)
    if os.path.exists('client_secrets.json'):
        with open('client_secrets.json', 'r') as f:
            return json.load(f)
    
    return None


# دالة الاتصال بجوجل درايف باستخدام Service Account
@st.cache_resource
def authenticate_drive():
    """
    مصادقة مع Google Drive باستخدام Service Account
    يعمل على Streamlit Cloud والتنمية المحلية بدون الحاجة لمتصفح
    """
    try:
        # قراءة Service Account credentials
        service_account_info = get_service_account_credentials()
        
        if not service_account_info:
            st.sidebar.error("❌ ملف Service Account غير موجود")
            with st.sidebar.expander("كيفية الإعداد"):
                st.markdown("""
                **للتنمية المحلية:**
                1. افتح [Google Cloud Console](https://console.cloud.google.com/)
                2. أنشئ Service Account
                3. نزّل الملف JSON وسمّه `client_secrets.json`
                4. ضعه في مجلد التطبيق
                
                **للنشر على Streamlit Cloud:**
                راجع ملف `DEPLOYMENT.md` لإعداد Streamlit Secrets
                """)
            return None
        
        # استخدام scope كامل للـ Drive (Service Account يحتاج صلاحيات أوسع)
        SCOPES = ['https://www.googleapis.com/auth/drive']
        
        # إنشاء credentials من Service Account
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, 
            scopes=SCOPES
        )
        
        # بناء service object
        service = build('drive', 'v3', credentials=creds)
        
        st.sidebar.success("✅ متصل بالدرايف")
        return service

    except Exception as e:
        st.sidebar.error("❌ فشل الاتصال بالدرايف")
        with st.sidebar.expander("عرض التفاصيل"):
            st.caption(f"الخطأ: {e}")
        return None


# دالة مشاركة المجلد مع بريد إلكتروني
def share_folder_with_email(service, folder_id: str, email: str):
    """
    مشاركة مجلد في Google Drive مع بريد إلكتروني محدد
    """
    if not service or not folder_id or not email:
        return False
    
    try:
        # إعداد صلاحيات المشاركة
        permission = {
            'type': 'user',
            'role': 'writer',  # صلاحيات كتابة وقراءة
            'emailAddress': email
        }
        
        # تنفيذ المشاركة
        service.permissions().create(
            fileId=folder_id,
            body=permission,
            fields='id',
            sendNotificationEmail=True  # إرسال إشعار بالبريد
        ).execute()
        
        st.sidebar.success(f"✅ تمت مشاركة المجلد مع: {email}")
        return True
        
    except Exception as e:
        st.sidebar.error(f"⚠️ فشلت المشاركة: {str(e)}")
        return False


# دالة البحث عن مجلد أو إنشاؤه في Google Drive
def find_or_create_folder(service, folder_name: str, share_with_email: str = None):
    """
    البحث عن مجلد في Google Drive، وإنشاؤه إذا لم يكن موجوداً
    يمكن مشاركته تلقائياً مع بريد إلكتروني
    """
    if service is None:
        return None

    try:
        # البحث عن المجلد
        query = (
            f"name='{folder_name}' and "
            "mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            folder_id = files[0]['id']
            st.sidebar.success(f"✅ تم العثور على المجلد: {folder_name}")
            
            # مشاركة المجلد إذا تم تحديد بريد إلكتروني
            if share_with_email and share_with_email.strip():
                share_folder_with_email(service, folder_id, share_with_email.strip())
            
            return folder_id
        
        # المجلد غير موجود - إنشاؤه
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        st.sidebar.success(f"✨ تم إنشاء المجلد الجديد: {folder_name}")
        
        # مشاركة المجلد إذا تم تحديد بريد إلكتروني
        if share_with_email and share_with_email.strip():
            share_folder_with_email(service, folder_id, share_with_email.strip())
        
        return folder_id
        
    except Exception as e:
        error_msg = str(e)
        
        # معالجة أخطاء SSL
        if "SSL" in error_msg or "WRONG_VERSION_NUMBER" in error_msg:
            st.sidebar.error("❌ خطأ في الاتصال بالإنترنت")
            with st.sidebar.expander("حلول مقترحة"):
                st.markdown("""
                - تأكد من اتصالك بالإنترنت
                - حاول إعادة تحميل الصفحة
                - إذا كنت خلف Proxy، قد تحتاج لإعدادات إضافية
                """)
        else:
            st.sidebar.error(f"❌ خطأ: {error_msg}")
        
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

        # إنشاء طبقة النص في PDF
        text_layer = io.BytesIO()
        c = canvas.Canvas(text_layer, pagesize=landscape(A4))
        
        # الكتابة على الطبقة الشفافة
        c.setFont("ArabicFont", font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x_pos, y_pos, bidi_text)
        c.save()
        text_layer.seek(0)
        
        # قراءة PDF القالب وطبقة النص
        template_pdf = PdfReader(template_path)
        text_pdf = PdfReader(text_layer)
        
        # دمج الطبقات (Overlay)
        writer = PdfWriter()
        page = template_pdf.pages[0]
        page.merge_page(text_pdf.pages[0])
        writer.add_page(page)
        
        # حفظ الناتج في BytesIO
        packet = io.BytesIO()
        writer.write(packet)
        packet.seek(0)

        # 3. إعداد بيانات الملف للرفع على جوجل درايف
        file_name = f"شهادة {name}.pdf"
        file_metadata = {
            "name": file_name,
            "parents": [drive_folder_id],
            "mimeType": "application/pdf",
        }

        # تنفيذ الرفع
        media = MediaIoBaseUpload(packet, mimetype='application/pdf', resumable=True)
        uploaded_file = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # تحديث شريط التقدم
        progress = (index + 1) / total
        progress_bar.progress(progress)
        st.info(f"تم رفع: {file_name}")

    st.balloons()
    st.success(f"✅ تم الانتهاء! تم إنشاء ورفع {total} شهادة إلى جوجل درايف.")
    shutil.rmtree(FOLDER_NAME, ignore_errors=True)


# ====================================================================
# Custom CSS للتصميم الجميل
# ====================================================================

st.markdown("""
<style>
    /* تحسين المظهر العام */
    .main {
        padding: 2rem 1rem;
    }
    
    /* تحسين العنوان */
    h1 {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    
    /* تحسين العناوين الفرعية */
    h3 {
        color: #2c3e50;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    /* تحسين الأزرار */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* تحسين file uploader */
    [data-testid="stFileUploader"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        border: 2px dashed #dee2e6;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #667eea;
        background-color: #f0f2ff;
    }
    
    /* تحسين sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem 1rem;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #6c757d;
        font-size: 0.9rem;
        padding: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* تحسين number inputs */
    [data-testid="stNumberInput"] {
        background-color: white;
        border-radius: 8px;
    }
    
    /* تحسين المسافات */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* تحسين رسائل النجاح */
    .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* تحسين رسائل الخطأ */
    .stError {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* تحسين Progress Bar */
    .stProgress > div > div {
        background-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# واجهة المستخدم (UI)
# ====================================================================

st.title("🎓 مولد الشهادات")
st.markdown("###")

# ====================================================================
# Sidebar - الإعدادات
# ====================================================================

st.sidebar.header("⚙️ الإعدادات")

st.sidebar.markdown("---")

# المصادقة
drive_service = authenticate_drive()

# إدخال اسم المجلد
DRIVE_TARGET_FOLDER = st.sidebar.text_input(
    "📁 اسم المجلد",
    value="شهادات الكورس",
    help="اسم المجلد في Google Drive (سيُنشأ تلقائياً إذا لم يكن موجوداً)"
)

# إدخال البريد الإلكتروني لمشاركة المجلد (اختياري)
user_email = st.sidebar.text_input(
    "📧 بريدك الإلكتروني (اختياري)",
    placeholder="example@gmail.com",
    help="لمشاركة المجلد معك تلقائياً (يعمل مع Service Account)"
)

# البحث عن/إنشاء المجلد (مع المشاركة إذا تم إدخال بريد)
drive_folder_id = (
    find_or_create_folder(drive_service, DRIVE_TARGET_FOLDER, user_email) if drive_service else None
)

# عرض رابط المجلد مع زرار النسخ
if drive_folder_id:
    folder_url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
    
    st.sidebar.success("✅ المجلد جاهز")
    
    # عرض الرابط مع أيقونة النسخ
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        st.markdown(f"[🔗 فتح المجلد]({folder_url})")
    with col2:
        if st.button("📋", key="copy_link", help="نسخ رابط المجلد"):
            st.sidebar.code(folder_url, language=None)
            st.sidebar.caption("✅ انسخ الرابط من الأعلى")
    
st.sidebar.markdown("---")

# قسم رفع الملفات - بتصميم columns
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📁 ملف الأسماء")
    uploaded_csv = st.file_uploader(
        "CSV أو Excel",
        type=["csv", "xlsx"],
        help="أول عمود يجب أن يحتوي على الأسماء"
    )

with col2:
    st.markdown("### 📄 قالب PDF")
    uploaded_template = st.file_uploader(
        "ملف PDF القالب",
        type=["pdf"],
        help="الشهادة الفارغة بدون أسماء"
    )

st.markdown("###")

# إعدادات الإحداثيات
st.markdown("### ⚙️ إحداثيات الاسم")
col1, col2, col3 = st.columns(3)

with col1:
    x_position = st.number_input(
        "المحاذاة الأفقية (X)",
        value=421,
        help="421 = المنتصف"
    )

with col2:
    y_position = st.number_input(
        "الارتفاع (Y)",
        value=350,
        help="المسافة من الأسفل"
    )

with col3:
    font_size = st.number_input(
        "حجم الخط",
        value=40,
        min_value=10,
        max_value=120
    )

st.markdown("###")

# زر البدء - كبير وجذاب
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    start_button = st.button("🚀 إنشاء ورفع الشهادات", type="primary", use_container_width=True)

if start_button:
    # التحقق من المتطلبات
    if drive_service is None:
        st.error("❌ يرجى المصادقة مع Google Drive أولاً")
    elif drive_folder_id is None:
        st.error(f"❌ فشل الوصول إلى المجلد '{DRIVE_TARGET_FOLDER}'")
    elif uploaded_csv is None or uploaded_template is None:
        st.warning("⚠️ يرجى رفع ملف الأسماء والقالب أولاً")
    elif not os.path.exists(FONT_PATH):
        st.error(f"❌ ملف الخط العربي غير موجود: {FONT_PATH}")
    else:
        # قراءة ملف الأسماء
        if uploaded_csv.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded_csv)
        else:
            df = pd.read_csv(uploaded_csv)

        # حفظ ملف PDF القالب مؤقتاً
        template_filename = "temp_template.pdf"
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


