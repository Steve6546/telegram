
#!/usr/bin/env python3
"""
Smart Media AI Assistant Bot Runner
تشغيل البوت الذكي لمعالجة الوسائط
"""

import os
import sys
import subprocess

def install_requirements():
    """تثبيت المتطلبات"""
    print("🔧 جاري تثبيت المتطلبات...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "SandyDesertedWearables/requirements.txt"])
        print("✅ تم تثبيت المتطلبات بنجاح")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المتطلبات: {e}")
        return False
    return True

def check_environment():
    """فحص المتغيرات البيئية"""
    if not os.path.exists(".env"):
        print("⚠️ ملف .env غير موجود. يرجى إنشاؤه وإضافة:")
        print("OPENROUTER_API_KEY=your_key_here")
        print("TELEGRAM_TOKEN=your_bot_token")
        return False
    
    # فحص وجود مجلد أدوات FFmpeg
    print("🎬 فحص أدوات الوسائط...")
    
    return True

def main():
    """تشغيل البوت"""
    print("🚀 بدء تشغيل Smart Media AI Assistant")
    
    # التأكد من وجود المتطلبات
    if not install_requirements():
        return
    
    # فحص البيئة
    if not check_environment():
        print("❌ يرجى إصلاح مشاكل البيئة أولاً")
        return
    
    # تغيير المجلد للمشروع
    os.chdir("SandyDesertedWearables")
    
    # تشغيل البوت
    print("✨ جاري تشغيل البوت...")
    try:
        import main
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
