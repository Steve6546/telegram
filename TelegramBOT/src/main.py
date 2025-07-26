# -*- coding: utf-8 -*-
"""
Main file for the Smart Media AI Assistant Bot.
الملف الرئيسي لبوت مساعد الوسائط الذكي.
"""

import os
import json
import telebot
from dotenv import load_dotenv
import time
import threading
import logging

# Import local modules
from .yt_dlp_wrapper import downloader
from . import handlers

# --- Setup ---
# Ensure log directory exists before configuring logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
load_dotenv()

# --- Bot Initialization ---
try:
    with open("config.json", "r", encoding='utf-8') as f:
        config = json.load(f)
    TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
    if not TELEGRAM_TOKEN:
        raise ValueError("التوكين غير موجود في config.json")
except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
    logger.error(f"❌ خطأ في قراءة ملف config.json: {e}")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- State and Statistics Management ---
start_time = time.time()
completed_operations = 0
error_count = 0
user_states = {}
user_preferences = {}
user_statistics = {}

def get_completed_operations():
    return completed_operations

def count_downloaded_files():
    downloads_dir = "media/downloads"
    if os.path.exists(downloads_dir):
        return len([f for f in os.listdir(downloads_dir) if os.path.isfile(os.path.join(downloads_dir, f))])
    return 0

def increment_operation():
    global completed_operations
    completed_operations += 1

def log_error(error_msg):
    global error_count
    error_count += 1
    logger.error(f"❌ خطأ: {error_msg}")
    with open("logs/error_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.ctime()}: {error_msg}\n")

# --- Core Bot Logic ---

def handle_download_request(chat_id, user_id, url, download_type):
    """معالجة طلبات التحميل المحسنة مع إحصائيات"""
    try:
        start_time_op = time.time()
        progress_msg = bot.send_message(chat_id, "⚡ جاري التحميل...")

        if user_id not in user_statistics:
            user_statistics[user_id] = {'downloads': 0, 'total_size': 0, 'last_download': None, 'favorite_quality': 'best'}

        download_path = "media/downloads"
        result = None

        if download_type.startswith("download_format_"):
            format_id = download_type.replace("download_format_", "")
            bot.edit_message_text(f"📥 جاري تحميل الفيديو بالصيغة {format_id}...", chat_id, progress_msg.message_id)
            result = downloader.download_with_format_id(url, format_id, download_path)
        elif download_type.startswith("download_audio_format_"):
            format_id = download_type.replace("download_audio_format_", "")
            bot.edit_message_text(f"🎵 جاري تحميل الصوت بالصيغة {format_id}...", chat_id, progress_msg.message_id)
            result = downloader.download_with_format_id(url, format_id, download_path)
        elif download_type == "download_best" or download_type == "smart_download":
            bot.edit_message_text("🧠 جاري التحميل الذكي بأفضل جودة...", chat_id, progress_msg.message_id)
            result = downloader.download_video(url, download_path, "best")
        elif download_type.startswith("download_audio"):
            bot.edit_message_text("🎵 جاري تحميل الصوت...", chat_id, progress_msg.message_id)
            result = downloader.download_audio(url, download_path)
        else:
            quality_map = {
                "download_4k": "4k", "quality_4k": "4k", "quality_8k": "8k",
                "download_1440p": "1440", "quality_2k": "1440",
                "download_1080p": "1080", "quality_1080p": "1080",
                "download_720p": "720", "quality_720p": "720",
                "download_480p": "480", "quality_480p": "480", 
                "download_360p": "360", "quality_360p": "360"
            }
            quality = quality_map.get(download_type, "best")
            bot.edit_message_text(f"📥 جاري تحميل الفيديو بجودة {quality}...", chat_id, progress_msg.message_id)
            result = downloader.download_video(url, download_path, quality)

        if result and result.get('success'):
            operation_time = time.time() - start_time_op
            increment_operation()
            user_statistics[user_id]['downloads'] += 1
            user_statistics[user_id]['last_download'] = time.time()
            if result.get('filesize_mb'):
                user_statistics[user_id]['total_size'] += result['filesize_mb']
            
            success_msg = f"✅ تم التحميل بنجاح! ⏱️ {operation_time:.1f}ث"
            bot.edit_message_text(success_msg, chat_id, progress_msg.message_id)
            send_downloaded_file(chat_id, result)
        else:
            error_msg = result.get('error', 'خطأ غير معروف') if result else 'فشل التحميل'
            log_error(f"فشل تحميل للمستخدم {user_id}: {error_msg}")
            bot.edit_message_text(f"❌ فشل التحميل: {error_msg}", chat_id, progress_msg.message_id)

    except Exception as e:
        log_error(f"خطأ في التحميل: {str(e)}")
        bot.send_message(chat_id, f"❌ خطأ في التحميل: {str(e)}")

def send_downloaded_file(chat_id, result):
    """إرسال الملف المحمل مع تحسينات"""
    try:
        filepath = result.get('filepath')
        filename = result.get('filename', 'file')

        if not filepath or not os.path.exists(filepath):
            bot.send_message(chat_id, "❌ لم يتم العثور على الملف المحمل")
            return

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

        if file_size_mb > 50:
            bot.send_message(chat_id, f"❌ **الملف كبير جداً للإرسال!**\n📊 **حجم الملف:** {file_size_mb:.1f} MB")
            return

        with open(filepath, 'rb') as file:
            caption = f"**{result.get('title', filename)}**\n📊 {file_size_mb:.1f} MB"
            if filepath.endswith(('.mp3', '.m4a', '.wav', '.aac')):
                bot.send_audio(chat_id, file, caption=f"🎵 {caption}", parse_mode='Markdown')
            elif filepath.endswith(('.mp4', '.avi', '.mkv', '.webm', '.mov')):
                bot.send_video(chat_id, file, caption=f"🎬 {caption}", parse_mode='Markdown')
            elif filepath.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                bot.send_photo(chat_id, file, caption=f"🖼️ {caption}")
            else:
                bot.send_document(chat_id, file, caption=f"📁 {caption}", parse_mode='Markdown')
        
        try:
            os.remove(filepath)
        except Exception as e:
            logger.error(f"Could not remove file {filepath}: {e}")

    except Exception as e:
        log_error(f"خطأ في إرسال الملف: {str(e)}")
        bot.send_message(chat_id, f"❌ خطأ في إرسال الملف: {str(e)}")

# --- System Maintenance ---

def cleanup_old_files():
    """تنظيف الملفات القديمة تلقائياً"""
    # Implementation for cleaning up old files
    pass

def start_cleanup_scheduler():
    """بدء جدولة التنظيف التلقائي"""
    # Implementation for cleanup scheduler
    pass

# --- Main Execution ---

if __name__ == "__main__":
    try:
        logger.info("🚀 بدء تشغيل Smart Media AI Assistant...")
        os.makedirs("media/downloads", exist_ok=True)
        os.makedirs("media/uploads", exist_ok=True)
        os.makedirs("media/processed", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        logger.info("📁 تم إنشاء المجلدات الضرورية")

        handlers.register_handlers()
        start_cleanup_scheduler()
        
        logger.info("🎉 تم تشغيل البوت بنجاح! جاهز لاستقبال الطلبات...")
        bot.infinity_polling(none_stop=True, interval=1, timeout=60)

    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ مميت في تشغيل البوت: {e}")
    finally:
        cleanup_old_files()
        logger.info("🛑 إغلاق Smart Media AI Assistant")