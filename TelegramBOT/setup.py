
#!/usr/bin/env python3
"""
إعداد مشروع Smart Media AI Assistant
"""

import os
import json

def setup_project():
    """إعداد المشروع"""
    print("🔧 إعداد Smart Media AI Assistant...")
    
    # إنشاء المجلدات المطلوبة
    folders = [
        "SandyDesertedWearables/downloads",
        "SandyDesertedWearables/uploads", 
        "SandyDesertedWearables/processed"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 تم إنشاء مجلد: {folder}")
    
    # إنشاء ملف .env إذا لم يكن موجوداً
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write("# Smart Media AI Assistant Environment Variables\n")
            f.write("OPENROUTER_API_KEY=your_openrouter_api_key_here\n")
            f.write("TELEGRAM_TOKEN=7836128954:AAGKYbv5w431lC5TCYRtiOimEocF1_anzn8\n")
        print("📝 تم إنشاء ملف .env")
    
    print("✅ تم إعداد المشروع بنجاح!")
    print("\n📋 الخطوات التالية:")
    print("1. قم بتحديث مفاتيح API في ملف .env")
    print("2. شغل البوت باستخدام: python run.py")

if __name__ == "__main__":
    setup_project()
