#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت توليد OAuth Token لـ Google Drive
========================================

هذا السكريبت يساعدك في توليد OAuth token مرة واحدة فقط.
Token سيُستخدم للرفع على Google Drive من حسابك الشخصي.

الاستخدام:
----------
1. تأكد من وجود oauth_credentials.json في نفس المجلد
2. شغّل: python generate_token.py
3. سيفتح المتصفح لتسجيل الدخول
4. بعد الموافقة، سيُنشأ ملف token.json
5. انسخ محتوى token.json إلى Streamlit Secrets

"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes المطلوبة
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def generate_token():
    """توليد OAuth token"""
    
    print("=" * 60)
    print("🔑 مولد OAuth Token لـ Google Drive")
    print("=" * 60)
    print()
    
    # التحقق من وجود oauth_credentials.json
    if not os.path.exists('oauth_credentials.json'):
        print("❌ خطأ: ملف oauth_credentials.json غير موجود!")
        print()
        print("الرجاء:")
        print("1. إنشاء OAuth Client ID من Google Cloud Console")
        print("2. تنزيل الملف JSON وتسميته oauth_credentials.json")
        print("3. وضعه في نفس المجلد مع هذا السكريبت")
        print()
        return
    
    creds = None
    
    # فحص token موجود
    if os.path.exists('token.json'):
        print("⚠️  ملف token.json موجود بالفعل!")
        response = input("هل تريد إعادة توليد token جديد؟ (y/n): ")
        if response.lower() != 'y':
            print("✅ تم الإلغاء.")
            return
        
        # حذف token القديم
        os.remove('token.json')
        print("🗑️  تم حذف token القديم.")
        print()
    
    try:
        print("📂 قراءة oauth_credentials.json...")
        
        # إنشاء OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'oauth_credentials.json', 
            SCOPES
        )
        
        print("✅ تم قراءة credentials بنجاح")
        print()
        print("🌐 سيتم فتح المتصفح الآن...")
        print("👉 سجّل دخول بحساب Google الذي تريد رفع الملفات فيه")
        print()
        
        # فتح المتصفح وطلب الموافقة
        creds = flow.run_local_server(port=0)
        
        # حفظ token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print()
        print("=" * 60)
        print("✅ تم توليد Token بنجاح!")
        print("=" * 60)
        print()
        print("📄 تم حفظ Token في: token.json")
        print()
        print("📋 الخطوات التالية:")
        print("-" * 60)
        print("1. افتح ملف token.json")
        print("2. انسخ المحتوى بالكامل")
        print("3. اذهب إلى Streamlit Cloud → Settings → Secrets")
        print("4. أضف:")
        print()
        print("   [google_drive_token]")
        print("   token = '''محتوى token.json هنا'''")
        print()
        print("5. احفظ وأعد تشغيل التطبيق")
        print("=" * 60)
        
        # عرض نموذج للمحتوى
        print()
        print("💡 معاينة token.json:")
        print("-" * 60)
        with open('token.json', 'r') as f:
            token_data = json.load(f)
            print(json.dumps(token_data, indent=2)[:500] + "...")
        print("-" * 60)
        
    except Exception as e:
        print()
        print("❌ حدث خطأ:")
        print(f"   {str(e)}")
        print()
        print("💡 تأكد من:")
        print("   - تفعيل Google Drive API في Google Cloud Console")
        print("   - ملف oauth_credentials.json صحيح")
        print()

if __name__ == '__main__':
    generate_token()

