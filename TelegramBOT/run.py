#!/usr/bin/env python3
"""
Smart Media AI Assistant Bot Runner
تشغيل البوت الذكي لمعالجة الوسائط
"""

import os
import sys
import subprocess

# Get the absolute path of the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

def install_requirements():
    """تثبيت المتطلبات"""
    print("🔧 جاري تحديث أدوات التثبيت...")
    try:
        # First, upgrade pip, setuptools, and wheel
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
        print("✅ تم تحديث أدوات التثبيت بنجاح")
        
        print("🔧 جاري تثبيت متطلبات المشروع...")
        requirements_path = os.path.join(script_dir, "requirements.txt")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ تم تثبيت المتطلبات بنجاح")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المتطلبات: {e}")
        return False
    return True

def check_environment():
    """فحص المتغيرات البيئية"""
    if not os.path.exists(os.path.join(script_dir, "config.json")):
        print("⚠️ ملف config.json غير موجود. يرجى إنشاؤه من config.json.example")
        return False
    return True

def main():
    """تشغيل البوت"""
    # Change the current working directory to the script's directory
    os.chdir(script_dir)
    
    print("🚀 بدء تشغيل Smart Media AI Assistant")
    
    if not install_requirements():
        return
    
    if not check_environment():
        print("❌ يرجى إصلاح مشاكل البيئة أولاً")
        return
    
    print("✨ جاري تشغيل البوت...")
    try:
        # Execute the main module as a package to solve relative import issues
        subprocess.run([sys.executable, "-m", "src.main"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت بواسطة المستخدم")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")

if __name__ == "__main__":
    main()
