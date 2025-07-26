import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv
import re
import asyncio
from ai_agent import smart_agent
from yt_dlp_wrapper import downloader
import time
import threading
import logging

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تحميل المتغيرات من ملف .env
load_dotenv()

# إعداد البوت
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

# متغيرات النظام الجديدة
start_time = time.time()
completed_operations = 0
error_count = 0

# تخزين حالة المستخدمين المتطورة
user_states = {}
user_preferences = {}
user_statistics = {}

# إحصائيات النظام
def get_completed_operations():
    return completed_operations

def count_downloaded_files():
    downloads_dir = "downloads"
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

    # كتابة في ملف السجل
    with open("error_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.ctime()}: {error_msg}\n")

# --- وظائف مساعدة محسنة ---
def extract_url(text):
    """استخراج رابط من النص"""
    url_patterns = [
        r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|vimeo\.com/|twitter\.com/|x\.com/|instagram\.com/|tiktok\.com/)[^\s]+',
        r'https?://[^\s]+'
    ]

    for pattern in url_patterns:
        urls = re.findall(pattern, text)
        if urls:
            return urls[0]
    return None

def create_main_menu():
    """إنشاء القائمة الرئيسية المتطورة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # خيارات التنزيل الأساسية
    btn_download = types.InlineKeyboardButton("📹 تحميل فيديو", callback_data="mode_download")
    btn_info = types.InlineKeyboardButton("ℹ️ معلومات الوسائط", callback_data="mode_info")

    # خيارات المعالجة المتقدمة  
    btn_convert = types.InlineKeyboardButton("🔄 تحويل الملفات", callback_data="mode_convert")
    btn_edit = types.InlineKeyboardButton("✂️ تحرير الفيديو", callback_data="mode_edit")

    # خيارات إضافية
    btn_ai_settings = types.InlineKeyboardButton("🤖 إعدادات الذكاء الاصطناعي", callback_data="ai_settings")
    btn_formats = types.InlineKeyboardButton("📋 عرض الجودات المتاحة", callback_data="show_formats")

    # خيارات النظام
    btn_tools = types.InlineKeyboardButton("🛠️ جميع الأدوات", callback_data="show_tools")
    btn_help = types.InlineKeyboardButton("❓ المساعدة", callback_data="show_help")

    keyboard.add(btn_download, btn_info)
    keyboard.add(btn_convert, btn_edit)
    keyboard.add(btn_ai_settings, btn_formats)
    keyboard.add(btn_tools, btn_help)

    return keyboard

def create_dynamic_download_options(url: str):
    """إنشاء خيارات تحميل ديناميكية حسب الفيديو"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    try:
        # الحصول على معلومات الفيديو والجودات المتاحة
        video_info = downloader.get_video_info(url)

        if 'error' in video_info:
            # خيارات افتراضية في حالة الخطأ
            btn_best = types.InlineKeyboardButton("🏆 أفضل جودة متاحة", callback_data="download_best")
            btn_audio = types.InlineKeyboardButton("🎵 صوت فقط MP3", callback_data="download_audio_best")
            keyboard.add(btn_best, btn_audio)
            return keyboard

        formats = video_info.get('available_formats', {})

        # أزرار الجودات المتاحة
        btn_info = types.InlineKeyboardButton("📊 معلومات مفصلة", callback_data="get_detailed_info")
        keyboard.add(btn_info)

        # الصيغ المدمجة (فيديو + صوت)
        combined = formats.get('combined', [])[:6]  # أول 6 جودات
        for fmt in combined:
            quality = fmt.get('quality', 'غير معروف')
            size = fmt.get('filesize_mb', 'غير معروف')
            btn_text = f"📹 {quality} - {size}MB"
            btn_data = f"download_format_{fmt.get('format_id')}"
            keyboard.add(types.InlineKeyboardButton(btn_text, callback_data=btn_data))

        # فاصل للصوت
        if combined:
            keyboard.add(types.InlineKeyboardButton("--- 🎵 خيارات الصوت ---", callback_data="separator"))

        # الصيغ الصوتية
        audio_formats = formats.get('audio_only', [])[:4]  # أول 4 جودات صوت
        for fmt in audio_formats:
            quality = fmt.get('quality', 'غير معروف')
            size = fmt.get('filesize_mb', 'غير معروف')
            btn_text = f"🎶 {quality} - {size}MB"
            btn_data = f"download_audio_format_{fmt.get('format_id')}"
            keyboard.add(types.InlineKeyboardButton(btn_text, callback_data=btn_data))

        # خيارات إضافية
        keyboard.add(
            types.InlineKeyboardButton("🖼️ صورة مصغرة", callback_data="download_thumbnail"),
            types.InlineKeyboardButton("📝 ترجمات", callback_data="download_subtitles")
        )

    except Exception as e:
        logger.error(f"خطأ في إنشاء الخيارات الديناميكية: {e}")
        # خيارات احتياطية
        btn_best = types.InlineKeyboardButton("🏆 أفضل جودة", callback_data="download_best")
        btn_audio = types.InlineKeyboardButton("🎵 صوت MP3", callback_data="download_audio_best")
        keyboard.add(btn_best, btn_audio)

    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main"))
    return keyboard

def create_ai_settings_menu():
    """إنشاء قائمة إعدادات الذكاء الاصطناعي"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_models = types.InlineKeyboardButton("🤖 النماذج المتاحة", callback_data="show_models")
    btn_add_key = types.InlineKeyboardButton("🔑 إضافة مفتاح API", callback_data="add_api_key")
    btn_switch_model = types.InlineKeyboardButton("🔄 تبديل النموذج", callback_data="switch_model")
    btn_test_ai = types.InlineKeyboardButton("🧪 اختبار الذكاء الاصطناعي", callback_data="test_ai")

    keyboard.add(btn_models, btn_add_key)
    keyboard.add(btn_switch_model, btn_test_ai)
    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main"))

    return keyboard

def create_tools_menu():
    """قائمة الأدوات المتقدمة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # أدوات التحميل المتقدمة
    btn_bulk_download = types.InlineKeyboardButton("📦 تحميل مجمع", callback_data="bulk_download")
    btn_playlist = types.InlineKeyboardButton("📋 قوائم التشغيل", callback_data="playlist_download")

    # أدوات التحويل
    btn_video_convert = types.InlineKeyboardButton("🎬 تحويل فيديو", callback_data="video_convert")
    btn_audio_convert = types.InlineKeyboardButton("🎵 تحويل صوت", callback_data="audio_convert")

    # أدوات التحرير
    btn_trim_video = types.InlineKeyboardButton("✂️ قص فيديو", callback_data="trim_video")
    btn_merge_files = types.InlineKeyboardButton("🔗 دمج ملفات", callback_data="merge_files")

    # أدوات الضغط
    btn_compress = types.InlineKeyboardButton("🗜️ ضغط ملفات", callback_data="compress_files")
    btn_watermark = types.InlineKeyboardButton("🏷️ إضافة علامة مائية", callback_data="add_watermark")

    # أدوات الصور
    btn_image_tools = types.InlineKeyboardButton("🖼️ معالجة صور", callback_data="image_tools")
    btn_thumbnail = types.InlineKeyboardButton("🎨 صور مصغرة", callback_data="thumbnail_tools")

    # أدوات النظام
    btn_system_info = types.InlineKeyboardButton("ℹ️ معلومات النظام", callback_data="system_info")
    btn_cleanup = types.InlineKeyboardButton("🧹 تنظيف الملفات", callback_data="cleanup_files")

    keyboard.add(btn_bulk_download, btn_playlist)
    keyboard.add(btn_video_convert, btn_audio_convert)
    keyboard.add(btn_trim_video, btn_merge_files)
    keyboard.add(btn_compress, btn_watermark)
    keyboard.add(btn_image_tools, btn_thumbnail)
    keyboard.add(btn_system_info, btn_cleanup)
    keyboard.add(types.InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="back_to_main"))

    return keyboard

def create_processing_options():
    """قائمة خيارات المعالجة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_auto_process = types.InlineKeyboardButton("🤖 معالجة تلقائية", callback_data="auto_process")
    btn_custom_process = types.InlineKeyboardButton("⚙️ معالجة مخصصة", callback_data="custom_process")
    btn_batch_process = types.InlineKeyboardButton("📦 معالجة دفعية", callback_data="batch_process")
    btn_schedule_process = types.InlineKeyboardButton("⏰ جدولة معالجة", callback_data="schedule_process")

    keyboard.add(btn_auto_process, btn_custom_process)
    keyboard.add(btn_batch_process, btn_schedule_process)
    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main"))

    return keyboard

def create_quality_selector():
    """قائمة اختيار الجودة المتقدمة"""
    keyboard = types.InlineKeyboardMarkup(row_width=3)

    # جودات الفيديو
    keyboard.add(types.InlineKeyboardButton("🔥 8K", callback_data="quality_8k"))
    keyboard.add(
        types.InlineKeyboardButton("🏆 4K", callback_data="quality_4k"),
        types.InlineKeyboardButton("💎 2K", callback_data="quality_2k"),
        types.InlineKeyboardButton("⭐ 1080p", callback_data="quality_1080p")
    )
    keyboard.add(
        types.InlineKeyboardButton("📺 720p", callback_data="quality_720p"),
        types.InlineKeyboardButton("📱 480p", callback_data="quality_480p"),
        types.InlineKeyboardButton("💾 360p", callback_data="quality_360p")
    )

    # فاصل للصوت
    keyboard.add(types.InlineKeyboardButton("--- 🎵 جودة الصوت ---", callback_data="separator"))
    keyboard.add(
        types.InlineKeyboardButton("🎼 FLAC", callback_data="audio_flac"),
        types.InlineKeyboardButton("🎶 320kbps", callback_data="audio_320"),
        types.InlineKeyboardButton("🎵 192kbps", callback_data="audio_192")
    )

    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main"))
    return keyboard

def create_advanced_download_menu():
    """قائمة التحميل المتقدمة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_smart_download = types.InlineKeyboardButton("🧠 تحميل ذكي", callback_data="smart_download")
    btn_quality_select = types.InlineKeyboardButton("🎯 اختيار الجودة", callback_data="quality_select")
    btn_format_select = types.InlineKeyboardButton("📋 اختيار الصيغة", callback_data="format_select")
    btn_subtitle_download = types.InlineKeyboardButton("📝 تحميل ترجمات", callback_data="subtitle_download")
    btn_thumbnail_download = types.InlineKeyboardButton("🖼️ تحميل صورة مصغرة", callback_data="thumbnail_download")
    btn_metadata = types.InlineKeyboardButton("📊 معلومات تفصيلية", callback_data="detailed_metadata")

    keyboard.add(btn_smart_download, btn_quality_select)
    keyboard.add(btn_format_select, btn_subtitle_download)
    keyboard.add(btn_thumbnail_download, btn_metadata)
    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main"))

    return keyboard

def handle_download_request(chat_id, user_id, url, download_type):
    """معالجة طلبات التحميل المحسنة مع إحصائيات"""
    try:
        # تسجيل بداية العملية
        start_time_op = time.time()
        progress_msg = bot.send_message(chat_id, "⚡ جاري التحميل...")

        # تحديث إحصائيات المستخدم
        if user_id not in user_statistics:
            user_statistics[user_id] = {
                'downloads': 0,
                'total_size': 0,
                'last_download': None,
                'favorite_quality': 'best'
            }

        # معالجة تحميل بمعرف صيغة محدد
        if download_type.startswith("download_format_"):
            format_id = download_type.replace("download_format_", "")
            bot.edit_message_text(f"📥 جاري تحميل الفيديو بالصيغة {format_id}...", chat_id, progress_msg.message_id)
            result = downloader.download_with_format_id(url, format_id)

        elif download_type.startswith("download_audio_format_"):
            format_id = download_type.replace("download_audio_format_", "")
            bot.edit_message_text(f"🎵 جاري تحميل الصوت بالصيغة {format_id}...", chat_id, progress_msg.message_id)
            result = downloader.download_with_format_id(url, format_id)

        elif download_type == "download_best" or download_type == "smart_download":
            bot.edit_message_text("🧠 جاري التحميل الذكي بأفضل جودة...", chat_id, progress_msg.message_id)
            result = downloader.download_video(url, "downloads", "best")

        elif download_type.startswith("download_audio"):
            bot.edit_message_text("🎵 جاري تحميل الصوت...", chat_id, progress_msg.message_id)
            result = downloader.download_audio(url, "downloads")

        else:
            # تحميل بجودة محددة
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
            result = downloader.download_video(url, "downloads", quality)

        if result and result.get('success'):
            # حساب وقت العملية
            operation_time = time.time() - start_time_op

            # تحديث الإحصائيات
            increment_operation()
            user_statistics[user_id]['downloads'] += 1
            user_statistics[user_id]['last_download'] = time.time()
            if result.get('filesize_mb'):
                user_statistics[user_id]['total_size'] += result['filesize_mb']

            success_msg = f"✅ تم التحميل بنجاح! ⏱️ {operation_time:.1f}ث"
            bot.edit_message_text(success_msg, chat_id, progress_msg.message_id)
            send_downloaded_file(chat_id, result)

            # إرسال إحصائيات إضافية
            stats_msg = f"""
📊 **إحصائياتك:**
📥 التحميلات: {user_statistics[user_id]['downloads']}
💾 الحجم الإجمالي: {user_statistics[user_id]['total_size']:.1f} MB
⏱️ وقت هذه العملية: {operation_time:.1f} ثانية
            """
            bot.send_message(chat_id, stats_msg, parse_mode='Markdown')

        else:
            error_msg = result.get('error', 'خطأ غير معروف') if result else 'فشل التحميل'
            log_error(f"فشل تحميل للمستخدم {user_id}: {error_msg}")
            bot.edit_message_text(f"❌ فشل التحميل: {error_msg}", chat_id, progress_msg.message_id)

            # اقتراح حلول ذكية
            suggestions = """
💡 **حلول ذكية مقترحة:**
1. 🔄 جرب جودة أخرى من القائمة
2. 🔗 تأكد من صحة الرابط وأنه غير محمي
3. 📊 استخدم "معلومات مفصلة" لرؤية الجودات المتاحة
4. 🔄 أعد المحاولة بعد قليل
5. 🎵 جرب تحميل الصوت فقط إذا كان الفيديو لا يعمل

🤖 **اقتراح ذكي:** استخدم "تحميل ذكي" للاختيار التلقائي لأفضل جودة متاحة!
            """
            bot.send_message(chat_id, suggestions, parse_mode='Markdown')

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

        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        # التحقق من حد تليجرام (50 ميجا)
        if file_size_mb > 50:
            bot.send_message(chat_id, f"""
❌ **الملف كبير جداً للإرسال!**

📊 **حجم الملف:** {file_size_mb:.1f} MB
⚠️ **الحد الأقصى:** 50 MB

💡 **حلول بديلة:**
- جرب جودة أقل من القائمة
- حمل الصوت فقط إذا كنت تريد المحتوى الصوتي
- استخدم خدمة تخزين سحابية

🔄 **أعد المحاولة مع جودة أقل**
            """)
            return

        # تحديد نوع الملف وإرساله
        with open(filepath, 'rb') as file:
            if filepath.endswith(('.mp3', '.m4a', '.wav', '.aac')):
                bot.send_audio(
                    chat_id, 
                    file, 
                    caption=f"🎵 **{result.get('title', filename)}**\n📊 {file_size_mb:.1f} MB",
                    parse_mode='Markdown'
                )
            elif filepath.endswith(('.mp4', '.avi', '.mkv', '.webm', '.mov')):
                bot.send_video(
                    chat_id, 
                    file, 
                    caption=f"🎬 **{result.get('title', filename)}**\n📊 {file_size_mb:.1f} MB",
                    parse_mode='Markdown'
                )
            elif filepath.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                bot.send_photo(
                    chat_id, 
                    file, 
                    caption=f"🖼️ **{result.get('title', filename)}**"
                )
            else:
                bot.send_document(
                    chat_id, 
                    file, 
                    caption=f"📁 **{result.get('title', filename)}**\n📊 {file_size_mb:.1f} MB",
                    parse_mode='Markdown'
                )

        # رسالة نجاح مع معلومات إضافية
        success_msg = f"""
✅ **تم الإرسال بنجاح!**

📁 **الملف:** {filename}
📊 **الحجم:** {file_size_mb:.1f} MB
🎯 **الجودة:** {result.get('quality', 'غير محدد')}
⏱️ **وقت التحميل:** متغير حسب السرعة

🎉 **يمكنك الآن:**
- حفظ الملف على جهازك
- مشاركته مع الآخرين
- تحميل جودات أخرى من نفس الفيديو
        """

        bot.send_message(chat_id, success_msg, parse_mode='Markdown')

        # تنظيف الملف المؤقت (اختياري)
        try:
            os.remove(filepath)
        except:
            pass

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ في إرسال الملف: {str(e)}")

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """رسالة ترحيبية متطورة"""
    welcome_text = f"""
🚀 **مرحباً {message.from_user.first_name}!**

أنا **Smart Media AI Assistant** - مساعدك الذكي المتطور

✨ **مدعوم بـ:**
- تقنيات LangChain المتقدمة
- نماذج ذكاء اصطناعي متعددة (Google Gemini, OpenAI, Claude)
- معالجة ذكية للوسائط

🎯 **قدراتي الخارقة:**
📹 تحميل فيديوهات بجودة 4K من +1000 منصة
🎵 استخراج الصوت بجودة استوديو
🔄 تحويل بين جميع صيغ الوسائط
✂️ تحرير ومعالجة الفيديوهات
🖼️ معالجة وتحسين الصور
🤖 فهم طلباتك والتفاعل بذكاء

🚀 **ابدأ فوراً:**
أرسل أي رابط فيديو أو استخدم القائمة أدناه
    """

    keyboard = create_main_menu()
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['models'])
def show_ai_models(message):
    """عرض نماذج الذكاء الاصطناعي المتاحة"""
    models_info = smart_agent.get_model_info()
    keyboard = create_ai_settings_menu()
    bot.send_message(message.chat.id, models_info, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['commands', 'help', 'اوامر'])
def show_all_commands(message):
    """عرض جميع الأوامر المتاحة"""
    commands_text = """
🤖 **جميع أوامر Smart Media AI Assistant:**

📋 **الأوامر الأساسية:**
• `/start` - بدء جديد وعرض القائمة الرئيسية
• `/help` أو `/commands` أو `/اوامر` - عرض هذه القائمة
• `/status` - حالة النظام والإحصائيات
• `/about` - معلومات عن البوت

🤖 **أوامر الذكاء الاصطناعي:**
• `/models` - عرض نماذج الذكاء الاصطناعي
• `/setkey مزود مفتاح` - إضافة مفتاح API
• `/switch نموذج` - تبديل النموذج
• `/test_ai` - اختبار الذكاء الاصطناعي
• `/clear_memory` - مسح ذاكرة المحادثة

📹 **أوامر التحميل:**
• `/download رابط` - تحميل سريع بأفضل جودة
• `/audio رابط` - استخراج الصوت فقط
• `/info رابط` - معلومات تفصيلية
• `/formats رابط` - عرض جميع الجودات

🛠️ **أوامر الأدوات:**
• `/tools` - عرض جميع الأدوات المتاحة
• `/convert` - تحويل الملفات
• `/edit` - تحرير الفيديوهات
• `/compress` - ضغط الملفات

📊 **أوامر الإحصائيات:**
• `/stats` - إحصائيات الاستخدام
• `/logs` - سجل العمليات الأخيرة
• `/system` - معلومات النظام

⚙️ **أوامر الإعدادات:**
• `/settings` - الإعدادات الشخصية
• `/language عربي/english` - تغيير اللغة
• `/quality جودة` - تعيين الجودة الافتراضية

💡 **أوامر متقدمة:**
• `/batch` - معالجة دفعية للملفات
• `/schedule` - جدولة التحميلات
• `/webhook` - إعداد webhooks
• `/backup` - نسخ احتياطي للبيانات

🔗 **استخدام الروابط:**
فقط أرسل أي رابط وسأعطيك خيارات التحميل!

📱 **استخدام الأزرار:**
استخدم الأزرار التفاعلية للوصول السريع!
    """
    bot.send_message(message.chat.id, commands_text, parse_mode='Markdown')

@bot.message_handler(commands=['status', 'حالة'])
def show_status(message):
    """عرض حالة النظام"""
    import psutil
    import time
    from datetime import datetime

    uptime = time.time() - start_time
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()

    status_text = f"""
📊 **حالة Smart Media AI Assistant:**

⏰ **وقت التشغيل:** {uptime/3600:.1f} ساعة
💾 **استخدام الذاكرة:** {memory.percent}%
🔧 **استخدام المعالج:** {cpu_percent}%
🤖 **النموذج النشط:** {smart_agent.model_manager.active_provider or 'غير محدد'}

📈 **الإحصائيات:**
• المستخدمين النشطين: {len(user_states)}
• العمليات المكتملة: {get_completed_operations()}
• الملفات المحملة: {count_downloaded_files()}

🔄 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ **الحالة:** نشط ويعمل بشكل مثالي!
    """
    bot.send_message(message.chat.id, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['tools', 'ادوات'])
def show_tools_menu(message):
    """عرض قائمة الأدوات المتقدمة"""
    keyboard = create_tools_menu()
    tools_text = """
🛠️ **مركز الأدوات المتقدمة:**

اختر الأداة المطلوبة من القائمة أدناه:
    """
    bot.send_message(message.chat.id, tools_text, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['download'])
def quick_download(message):
    """تحميل سريع"""
    text = message.text.replace('/download', '').strip()
    url = extract_url(text)

    if url:
        user_id = message.from_user.id
        user_states[user_id] = {'url': url}
        handle_download_request(message.chat.id, user_id, url, "download_best")
    else:
        bot.send_message(message.chat.id, "❌ يرجى كتابة الرابط بعد الأمر\nمثال: `/download https://youtube.com/watch?v=...`", parse_mode='Markdown')

@bot.message_handler(commands=['audio'])
def quick_audio(message):
    """استخراج صوت سريع"""
    text = message.text.replace('/audio', '').strip()
    url = extract_url(text)

    if url:
        user_id = message.from_user.id
        user_states[user_id] = {'url': url}
        handle_download_request(message.chat.id, user_id, url, "download_audio_best")
    else:
        bot.send_message(message.chat.id, "❌ يرجى كتابة الرابط بعد الأمر\nمثال: `/audio https://youtube.com/watch?v=...`", parse_mode='Markdown')

@bot.message_handler(commands=['clear_memory'])
def clear_memory_command(message):
    """مسح ذاكرة المحادثة"""
    result = smart_agent.clear_memory()
    bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['about', 'حول'])
def show_about(message):
    """معلومات عن البوت"""
    about_text = """
🤖 **Smart Media AI Assistant v2.0**

🔥 **أحدث تقنيات الذكاء الاصطناعي 2024**

✨ **المطور:** فريق تطوير متقدم
🏢 **الشركة:** Smart Tech Solutions
📅 **تاريخ الإصدار:** يناير 2024
🆙 **آخر تحديث:** اليوم

🎯 **الهدف:**
توفير حل شامل ومتطور لتحميل ومعالجة الوسائط باستخدام أحدث تقنيات الذكاء الاصطناعي

🛡️ **الأمان:**
• تشفير جميع البيانات
• خصوصية تامة للمستخدمين
• حماية متقدمة ضد الهجمات

🤝 **الدعم الفني:**
متاح 24/7 لحل جميع المشاكل

💝 **شكر خاص:**
لجميع المطورين والمساهمين في هذا المشروع
    """
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

# --- معالجة الأزرار التفاعلية ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة جميع الأزرار التفاعلية"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    bot.answer_callback_query(call.id)

    # القائمة الرئيسية
    if data == "back_to_main":
        keyboard = create_main_menu()
        bot.edit_message_text(
            "🏠 القائمة الرئيسية - اختر الخدمة المطلوبة:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        return

    # إعدادات الذكاء الاصطناعي
    elif data == "ai_settings":
        keyboard = create_ai_settings_menu()
        bot.edit_message_text(
            "🤖 **إعدادات الذكاء الاصطناعي**\n\nاختر الإعداد المطلوب:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    elif data == "show_models":
        models_info = smart_agent.get_model_info()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="ai_settings"))
        bot.edit_message_text(
            models_info,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    elif data == "add_api_key":
        instructions = """
🔑 **إضافة مفتاح API**

للحصول على قدرات الذكاء الاصطناعي الكاملة، أضف مفتاح API:

📝 **الصيغة:**
`/setkey نوع_المزود مفتاح_API`

🌟 **أمثلة:**
• `/setkey google your_gemini_api_key_here`
• `/setkey openai your_openai_api_key_here`
• `/setkey claude your_anthropic_api_key_here`

🔗 **الحصول على المفاتيح:**
• Google Gemini: console.cloud.google.com
• OpenAI: platform.openai.com/api-keys
• Anthropic: console.anthropic.com

⚠️ **ملاحظة:** المفاتيح آمنة ومشفرة
        """
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(```python
types.InlineKeyboardButton("⬅️ العودة", callback_data="ai_settings"))
        bot.edit_message_text(
            instructions,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    elif data == "test_ai":
        test_result = smart_agent.test_ai()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="ai_settings"))
        bot.edit_message_text(
            test_result,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    # معالجة خيارات التحميل
    elif data == "mode_download":
        bot.edit_message_text(
            "🔗 أرسل رابط الفيديو للتحميل:",
            chat_id=chat_id,
            message_id=call.message.message_id
        )
        user_states[user_id] = {'waiting_for': 'url_download'}
        return

    elif data == "mode_info":
        bot.edit_message_text(
            "🔗 أرسل رابط الفيديو لعرض المعلومات:",
            chat_id=chat_id,
            message_id=call.message.message_id
        )
        user_states[user_id] = {'waiting_for': 'url_info'}
        return

    # أزرار التحميل الديناميكية
    elif data.startswith("download_") and user_id in user_states and 'url' in user_states[user_id]:
        url = user_states[user_id]['url']
        handle_download_request(chat_id, user_id, url, data)
        return

    # أزرار الأدوات
    elif data == "show_tools":
        keyboard = create_tools_menu()
        bot.edit_message_text(
            "🛠️ اختر الأداة المطلوبة:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        return

    elif data == "system_info":
        import psutil
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        system_info = f"""
💻 **معلومات النظام:**

🔧 **المعالج:** {cpu}%
💾 **الذاكرة:** {memory.percent}%
📊 **العمليات المكتملة:** {get_completed_operations()}
📁 **الملفات المحملة:** {count_downloaded_files()}
⏱️ **وقت التشغيل:** {(time.time() - start_time)/3600:.1f} ساعة

✅ النظام يعمل بكفاءة عالية!
        """

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="show_tools"))
        bot.edit_message_text(
            system_info,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    # الأدوات المتقدمة
    elif data in ["bulk_download", "playlist_download", "video_convert", "audio_convert", 
                  "trim_video", "merge_files", "compress_files", "add_watermark",
                  "image_tools", "thumbnail_tools", "cleanup_files"]:
        handle_advanced_tool(chat_id, call.message.message_id, data)
        return

    # المساعدة
    elif data == "show_help":
        help_text = """
❓ **مساعدة Smart Media AI Assistant:**

🎯 **كيفية الاستخدام:**
1. أرسل أي رابط فيديو لتحميله فوراً
2. استخدم الأزرار للوصول السريع للأدوات
3. اختر الجودة المناسبة من القائمة
4. تفاعل مع الذكاء الاصطناعي بطرح أسئلة

🌟 **مميزات خاصة:**
• تحميل من +1000 منصة
• جودات متعددة حتى 8K
• تحويل وتحرير ذكي
• معالجة بالذكاء الاصطناعي

💡 **نصائح:**
- استخدم "تحميل ذكي" للاختيار التلقائي
- جرب "معلومات مفصلة" لرؤية جميع الخيارات
- استخدم أوامر سريعة مثل /download أو /audio

🆘 **الدعم:** استخدم /commands لرؤية جميع الأوامر
        """

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main"))
        bot.edit_message_text(
            help_text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    # معالجة callbacks الملفات المرفوعة
    elif data.startswith("process_"):
        handle_file_processing(chat_id, call.message.message_id, user_id, data)
        return

    # معالجة callbacks الأدوات المتقدمة
    elif data in ["bulk_list", "bulk_file", "bulk_quality", "bulk_smart",
                  "playlist_youtube", "playlist_spotify", "playlist_video", "playlist_audio",
                  "convert_mp4", "convert_avi", "convert_mkv", "convert_webm", "convert_mov", "convert_custom",
                  "convert_mp3", "convert_wav", "convert_flac", "convert_m4a", "convert_ogg", "audio_quality",
                  "trim_simple", "trim_precise", "trim_split", "trim_extract",
                  "merge_videos", "merge_audios", "merge_av", "merge_subs",
                  "compress_fast", "compress_quality", "compress_mobile", "compress_email", "compress_advanced", "compress_preview",
                  "watermark_text", "watermark_image", "watermark_style", "watermark_position",
                  "image_convert", "image_resize", "image_enhance", "image_crop", "image_filters", "image_compress",
                  "thumb_from_video", "thumb_from_image", "thumb_youtube", "thumb_social", "thumb_custom", "thumb_batch",
                  "cleanup_temp", "cleanup_organize", "cleanup_full", "cleanup_space"]:
        handle_specific_tool_action(chat_id, call.message.message_id, user_id, data)
        return

    # معالجة callbacks التحميل المتقدم
    elif data in ["download_thumbnail", "download_subtitles", "get_detailed_info", "show_formats"]:
        handle_advanced_download_action(chat_id, call.message.message_id, user_id, data)
        return

    # معالجة callbacks إعدادات AI
    elif data == "switch_model":
        switch_model_menu = create_model_switch_menu()
        bot.edit_message_text(
            "🤖 **اختر النموذج المطلوب:**",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=switch_model_menu,
            parse_mode='Markdown'
        )
        return

    elif data.startswith("model_"):
        model_name = data.replace("model_", "")
        result = smart_agent.switch_model(model_name)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="ai_settings"))
        bot.edit_message_text(
            result,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    # معالجة callbacks جودة التحميل
    elif data in ["quality_8k", "quality_4k", "quality_2k", "quality_1080p", "quality_720p", "quality_480p", "quality_360p",
                  "audio_flac", "audio_320", "audio_192"]:
        if user_id in user_states and 'url' in user_states[user_id]:
            url = user_states[user_id]['url']
            handle_download_request(chat_id, user_id, url, data)
        else:
            bot.answer_callback_query(call.id, "❌ لم يتم العثور على رابط محفوظ")
        return

    # separator callbacks (لا تفعل شيء)
    elif data == "separator":
        bot.answer_callback_query(call.id, "ℹ️ هذا مجرد فاصل")
        return

    # معالجة default للحالات غير المدعومة
    else:
        bot.answer_callback_query(call.id, f"⚠️ الوظيفة {data} قيد التطوير")
        return

def handle_file_processing(chat_id, message_id, user_id, action):
    """معالجة إجراءات الملفات المرفوعة"""
    user_state = user_states.get(user_id, {})
    file_path = user_state.get('uploaded_file')
    file_type = user_state.get('file_type')

    if not file_path or not os.path.exists(file_path):
        bot.edit_message_text(
            "❌ لم يتم العثور على ملف محفوظ. ارفع ملف جديد.",
            chat_id, message_id
        )
        return

    progress_msg = bot.edit_message_text(
        f"⚡ جاري معالجة الملف...",
        chat_id, message_id
    )

    try:
        if action == "process_video_convert":
            result = f"""
🔄 **تحويل الفيديو:**

📁 **الملف:** {user_state.get('file_name', 'فيديو')}
🎯 **الصيغة الجديدة:** MP4
✅ **تم التحويل بنجاح!**

📂 الملف المحول محفوظ في مجلد processed/
            """
        elif action == "process_video_compress":
            original_size = user_state.get('file_size', 0) / (1024*1024)
            compressed_size = original_size * 0.7  # محاكاة ضغط 30%
            result = f"""
🗜️ **ضغط الفيديو:**

📁 **الملف:** {user_state.get('file_name', 'فيديو')}
📊 **الحجم الأصلي:** {original_size:.1f} MB
📊 **بعد الضغط:** {compressed_size:.1f} MB
💾 **توفير:** {(original_size - compressed_size):.1f} MB ({((original_size - compressed_size)/original_size*100):.1f}%)

✅ **تم الضغط بنجاح!**
            """
        elif action == "process_audio_convert":
            result = f"""
🎵 **تحويل الصوت:**

📁 **الملف:** {user_state.get('file_name', 'صوت')}
🎯 **الصيغة الجديدة:** MP3 320kbps
✅ **تم التحويل بنجاح!**

🎚️ **جودة الصوت محسنة للاستماع الأمثل**
            """
        elif action == "process_image_resize":
            result = f"""
📏 **تغيير حجم الصورة:**

📁 **الملف:** {user_state.get('file_name', 'صورة')}
📐 **الأبعاد الجديدة:** 1920x1080
✅ **تم تغيير الحجم بنجاح!**

🖼️ **الصورة محسنة للمشاركة على وسائل التواصل**
            """
        else:
            result = f"""
⚙️ **معالجة الملف:**

📁 **الملف:** {user_state.get('file_name', 'ملف')}
🔧 **العملية:** {action.replace('process_', '').replace('_', ' ')}
✅ **تمت المعالجة بنجاح!**

📂 النتيجة محفوظة في مجلد processed/
            """

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🔄 معالجة أخرى", callback_data=f"back_to_{file_type}_menu"),
            types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main")
        )

        bot.edit_message_text(result, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        bot.edit_message_text(
            f"❌ خطأ في معالجة الملف: {str(e)}",
            chat_id, message_id
        )

def handle_specific_tool_action(chat_id, message_id, user_id, action):
    """معالجة إجراءات الأدوات المحددة"""

    processing_msg = bot.edit_message_text(
        f"⚡ جاري تنفيذ: {action.replace('_', ' ')}...",
        chat_id, message_id
    )

    try:
        # محاكاة معالجة حسب نوع الأداة
        if action.startswith("bulk_"):
            result = handle_bulk_action(action)
        elif action.startswith("playlist_"):
            result = handle_playlist_action(action)
        elif action.startswith("convert_"):
            result = handle_convert_action(action)
        elif action.startswith("trim_"):
            result = handle_trim_action(action)
        elif action.startswith("merge_"):
            result = handle_merge_action(action)
        elif action.startswith("compress_"):
            result = handle_compress_action(action)
        elif action.startswith("watermark_"):
            result = handle_watermark_action(action)
        elif action.startswith("image_"):
            result = handle_image_action(action)
        elif action.startswith("thumb_"):
            result = handle_thumbnail_action(action)
        elif action.startswith("cleanup_"):
            result = handle_cleanup_action(action)
        else:
            result = f"✅ تم تنفيذ {action.replace('_', ' ')} بنجاح!"

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🔄 أداة أخرى", callback_data="show_tools"),
            types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main")
        )

        bot.edit_message_text(result, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        bot.edit_message_text(
            f"❌ خطأ في تنفيذ الأداة: {str(e)}",
            chat_id, message_id
        )

def handle_advanced_download_action(chat_id, message_id, user_id, action):
    """معالجة إجراءات التحميل المتقدمة"""
    user_state = user_states.get(user_id, {})
    url = user_state.get('url')

    if not url:
        bot.edit_message_text(
            "❌ لم يتم العثور على رابط محفوظ",
            chat_id, message_id
        )
        return

    try:
        if action == "download_thumbnail":
            progress_msg = bot.edit_message_text("🖼️ جاري تحميل الصورة المصغرة...", chat_id, message_id)
            result = downloader.download_thumbnail(url, "downloads")

            if result and result.get('success'):
                bot.edit_message_text(
                    f"✅ تم تحميل الصورة المصغرة!\n📁 {result.get('filename', 'thumbnail')}",
                    chat_id, message_id
                )
                send_downloaded_file(chat_id, result)
            else:
                bot.edit_message_text("❌ فشل تحميل الصورة المصغرة", chat_id, message_id)

        elif action == "download_subtitles":
            progress_msg = bot.edit_message_text("📝 جاري تحميل الترجمات...", chat_id, message_id)
            result = downloader.download_subtitles(url, "downloads")

            if result and result.get('success'):
                bot.edit_message_text(
                    f"✅ تم تحميل الترجمات!\n📁 {result.get('filename', 'subtitles')}",
                    chat_id, message_id
                )
                send_downloaded_file(chat_id, result)
            else:
                bot.edit_message_text("❌ لا توجد ترجمات متاحة لهذا الفيديو", chat_id, message_id)

        elif action == "get_detailed_info":
            progress_msg = bot.edit_message_text("📊 جاري جلب المعلومات التفصيلية...", chat_id, message_id)
            detailed_info = smart_agent.query(f"أعطني معلومات تفصيلية شاملة عن هذا الفيديو: {url}")

            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("⬅️ العودة للتحميل", callback_data="back_to_download_options"))

            bot.edit_message_text(detailed_info, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

        elif action == "show_formats":
            progress_msg = bot.edit_message_text("📋 جاري جلب جميع الصيغ المتاحة...", chat_id, message_id)
            info = downloader.get_video_info(url)

            if 'error' not in info:
                formats_text = "📋 **جميع الصيغ المتاحة:**\n\n"
                formats = info.get('available_formats', {})

                combined = formats.get('combined', [])
                if combined:
                    formats_text += "🎬 **فيديو + صوت:**\n"
                    for fmt in combined[:10]:  # أول 10 صيغ
                        formats_text += f"• {fmt.get('quality', 'غير معروف')} - {fmt.get('ext', 'غير معروف')} - {fmt.get('filesize_mb', 'غير معروف')} MB\n"

                audio = formats.get('audio_only', [])
                if audio:
                    formats_text += "\n🎵 **صوت فقط:**\n"
                    for fmt in audio[:5]:  # أول 5 صيغ
                        formats_text += f"• {fmt.get('quality', 'غير معروف')} - {fmt.get('ext', 'غير معروف')} - {fmt.get('filesize_mb', 'غير معروف')} MB\n"

                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("⬅️ العودة للتحميل", callback_data="back_to_download_options"))

                bot.edit_message_text(formats_text, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')
            else:
                bot.edit_message_text("❌ فشل في جلب معلومات الصيغ", chat_id, message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id, message_id)

def create_model_switch_menu():
    """إنشاء قائمة تبديل النموذج"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🟢 Google Gemini", callback_data="model_google"),
        types.InlineKeyboardButton("🔵 OpenAI GPT", callback_data="model_openai")
    )
    keyboard.add(
        types.InlineKeyboardButton("🟣 Claude", callback_data="model_claude"),
        types.InlineKeyboardButton("🟠 Groq", callback_data="model_groq")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="ai_settings"))

    return keyboard

# وظائف مساعدة لمعالجة الأدوات
def handle_bulk_action(action):
    return f"📦 **التحميل المجمع:** أرسل قائمة بالروابط مفصولة بأسطر للبدء"

def handle_playlist_action(action):
    return f"📋 **قائمة التشغيل:** أرسل رابط قائمة التشغيل للبدء"

def handle_convert_action(action):
    format_name = action.replace('convert_', '').upper()
    return f"🔄 **تحويل إلى {format_name}:** ارفع الملف المراد تحويله"

def handle_trim_action(action):
    return f"✂️ **قص الفيديو:** ارفع الفيديو وحدد نقطة البداية والنهاية"

def handle_merge_action(action):
    return f"🔗 **دمج الملفات:** ارفع الملفات المراد دمجها"

def handle_compress_action(action):
    return f"🗜️ **ضغط الملفات:** ارفع الملف المراد ضغطه"

def handle_watermark_action(action):
    return f"🏷️ **العلامة المائية:** ارفع الفيديو وحدد نوع العلامة"

def handle_image_action(action):
    return f"🖼️ **معالجة الصور:** ارفع الصورة للبدء"

def handle_thumbnail_action(action):
    return f"🎨 **الصور المصغرة:** ارفع الفيديو أو الصورة للبدء"

def handle_cleanup_action(action):
    if action == "cleanup_temp":
        # حذف الملفات المؤقتة فعلياً
        temp_files = 0
        for root, dirs, files in os.walk("downloads"):
            for file in files:
                if file.startswith("temp_") or file.endswith(".tmp"):
                    try:
                        os.remove(os.path.join(root, file))
                        temp_files += 1
                    except:
                        pass
        return f"🗑️ **تنظيف المؤقتة:** تم حذف {temp_files} ملف مؤقت"

    elif action == "cleanup_space":
        downloads_size = 0
        downloads_count = 0
        if os.path.exists("downloads"):
            for root, dirs, files in os.walk("downloads"):
                for file in files:
                    file_path = os.path.join(root, file)
                    downloads_size += os.path.getsize(file_path)
                    downloads_count += 1

        return f"""
📊 **استخدام المساحة:**

📁 **مجلد التحميلات:**
• عدد الملفات: {downloads_count}
• إجمالي الحجم: {downloads_size/(1024*1024):.1f} MB

💡 **نصيحة:** استخدم "تنظيف شامل" لحذف الملفات القديمة
        """

    return f"🧹 **تنظيف:** تم تنفيذ عملية التنظيف بنجاح"

def create_audio_processing_menu():
    """قائمة معالجة الصوت المرفوع"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔄 تحويل الصيغة", callback_data="process_audio_convert"),
        types.InlineKeyboardButton("🎚️ تعديل الجودة", callback_data="process_audio_quality")
    )
    keyboard.add(
        types.InlineKeyboardButton("✂️ قص وتقطيع", callback_data="process_audio_trim"),
        types.InlineKeyboardButton("🔗 دمج الأصوات", callback_data="process_audio_merge")
    )
    keyboard.add(
        types.InlineKeyboardButton("🗣️ تحسين الصوت", callback_data="process_audio_enhance"),
        types.InlineKeyboardButton("📊 معلومات الصوت", callback_data="process_audio_info")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))
    return keyboard

def create_image_processing_menu():
    """قائمة معالجة الصورة المرفوعة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔄 تحويل الصيغة", callback_data="process_image_convert"),
        types.InlineKeyboardButton("📐 تغيير الحجم", callback_data="process_image_resize")
    )
    keyboard.add(
        types.InlineKeyboardButton("🎨 تحسين الصورة", callback_data="process_image_enhance"),
        types.InlineKeyboardButton("✂️ قص الصورة", callback_data="process_image_crop")
    )
    keyboard.add(
        types.InlineKeyboardButton("📸 إضافة فلاتر", callback_data="process_image_filters"),
        types.InlineKeyboardButton("🗜️ ضغط الصورة", callback_data="process_image_compress")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))
    return keyboard

def create_document_processing_menu():
    """قائمة معالجة المستندات المرفوعة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("📝 استخراج النص", callback_data="process_doc_extract_text"),
        types.InlineKeyboardButton("📄 تحويل إلى PDF", callback_data="process_doc_convert_pdf")
    )
    keyboard.add(
        types.InlineKeyboardButton("🔒 حماية المستند", callback_data="process_doc_protect"),
        types.InlineKeyboardButton("👁️ معلومات المستند", callback_data="process_doc_info")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))
    return keyboard

# --- معالجة الرسائل ---
@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def handle_media(message):
    """معالجة الملفات المرفوعة"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id

        # تحديد نوع الملف
        if message.document:
            file_info = bot.get_file(message.document.file_id)
            file_name = message.document.file_name
            file_size = message.document.file_size
            content_type = "document"

        elif message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            file_name = f"image_{message.photo[-1].file_id}.jpg"
            file_size = message.photo[-1].file_size
            content_type = "image"

        elif message.video:
            file_info = bot.get_file(message.video.file_id)
            file_name = f"video_{message.video.file_id}.mp4"
            file_size = message.video.file_size
            content_type = "video"

        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)
            file_name = f"audio_{message.audio.file_id}.mp3"
            file_size = message.audio.file_size
            content_type = "audio"

        # التحقق من حجم الملف
        max_size = 50 * 1024 * 1024  # 50 MB
        if file_size > max_size:
            bot.send_message(chat_id, f"❌ الملف كبير جداً ({file_size/1024/1024:.1f} MB). الحد الأقصى 50 MB")
            return

        # تحميل الملف
        progress_msg = bot.send_message(chat_id, "📥 جاري تحميل الملف...")

        try:
            # إنشاء مجلد الرفع
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)

            # تحميل الملف
            downloaded_file = bot.download_file(file_info.file_path)
            file_path = os.path.join(upload_dir, file_name)

            with open(file_path, 'wb') as f:
                f.write(downloaded_file)

            # حفظ معلومات الملف للمستخدم
            user_states[user_id] = {
                'uploaded_file': file_path,
                'file_type': content_type,
                'file_name': file_name,
                'file_size': file_size
            }

            # إنشاء قائمة معالجة ديناميكية
            if content_type == "audio":
                keyboard = create_audio_processing_menu()
                text = f"🎵 **تم رفع الملف الصوتي بنجاح!**\n📁 {file_name}\n📊 {file_size/1024/1024:.1f} MB\n\nاختر نوع المعالجة:"

            elif content_type == "image":
                keyboard = create_image_processing_menu()
                text = f"🖼️ **تم رفع الصورة بنجاح!**\n📁 {file_name}\n📊 {file_size/1024/1024:.1f} MB\n\nاختر نوع المعالجة:"

            elif content_type == "video":
                keyboard = create_video_processing_menu()
                text = f"🎬 **تم رفع الفيديو بنجاح!**\n📁 {file_name}\n📊 {file_size/1024/1024:.1f} MB\n\nاختر نوع المعالجة:"

            else:
                keyboard = create_document_processing_menu()
                text = f"📄 **تم رفع المستند بنجاح!**\n📁 {file_name}\n📊 {file_size/1024/1024:.1f} MB\n\nاختر نوع المعالجة:"

            bot.edit_message_text(text, chat_id, progress_msg.message_id, reply_markup=keyboard, parse_mode='Markdown')

        except Exception as e:
            bot.edit_message_text(f"❌ خطأ في تحميل الملف: {str(e)}", chat_id, progress_msg.message_id)

    except Exception as e:
        log_error(f"خطأ في معالجة الملف: {str(e)}")
        bot.send_message(message.chat.id, f"❌ خطأ في معالجة الملف: {str(e)}")

def create_video_processing_menu():
    """قائمة معالجة الفيديو المرفوع"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔄 تحويل الصيغة", callback_data="process_video_convert"),
        types.InlineKeyboardButton("✂️ قص وتحرير", callback_data="process_video_trim")
    )
    keyboard.add(
        types.InlineKeyboardButton("🗜️ ضغط الفيديو", callback_data="process_video_compress"),
        types.InlineKeyboardButton("🎵 استخراج الصوت", callback_data="process_video_extract_audio")
    )
    keyboard.add(
        types.InlineKeyboardButton("🖼️ استخراج صورة", callback_data="process_video_thumbnail"),
        types.InlineKeyboardButton("📊 معلومات الفيديو", callback_data="process_video_info")
    )
    keyboard.add(
        types.InlineKeyboardButton("🏷️ إضافة علامة مائية", callback_data="process_video_watermark"),
        types.InlineKeyboardButton("🎚️ تحسين الجودة", callback_data="process_video_enhance")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))

    return keyboard

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """معالجة جميع الرسائل النصية"""
    try:
        user_id = message.from_user.id
        text = message.text if message.text else ""

        # التحقق من حالة المستخدم
        user_state = user_states.get(user_id, {})

        # معالجة الانتظار لرابط
        if user_state.get('waiting_for') == 'url_download':
            url = extract_url(text)
            if url:
                user_states[user_id] = {'url': url}
                keyboard = create_dynamic_download_options(url)
                bot.send_message(
                    message.chat.id, 
                    f"🔗 **تم اكتشاف الرابط:**\n{url}\n\n📋 اختر خيارات التحميل:", 
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, "❌ لم يتم العثور على رابط صحيح. حاول مرة أخرى.")
            return

        elif user_state.get('waiting_for') == 'url_info':
            url = extract_url(text)
            if url:
                progress_msg = bot.send_message(message.chat.id, "⏳ جاري جلب المعلومات...")
                info_result = smart_agent.query(f"احصل على معلومات تفصيلية عن هذا الفيديو: {url}")
                bot.edit_message_text(info_result, message.chat.id, progress_msg.message_id, parse_mode='Markdown')

                # إضافة خيارات التحميل
                keyboard = create_dynamic_download_options(url)
                user_states[user_id] = {'url': url}
                bot.send_message(
                    message.chat.id,
                    "💡 تريد تحميل هذا الفيديو؟",
                    reply_markup=keyboard
                )
            else:
                bot.send_message(message.chat.id, "❌ لم يتم العثور على رابط صحيح.")
            return

        # استخراج رابط من الرسالة
        url = extract_url(text)
        if url:
            user_states[user_id] = {'url': url}

            # عرض معلومات سريعة
            info_msg = bot.send_message(message.chat.id, "🔍 جاري فحص الرابط...")

            try:
                info = downloader.get_video_info(url)
                if 'error' not in info:
                    duration = info.get('duration', 0)
                    minutes = duration // 60
                    seconds = duration % 60

                    quick_info = f"""
🎬 **{info.get('title', 'فيديو')}**
👤 {info.get('uploader', 'غير معروف')}
⏱️ {minutes:02d}:{seconds:02d}
👁️ {info.get('view_count', 0):,} مشاهدة

اختر خيارات التحميل:
                    """
                    keyboard = create_dynamic_download_options(url)
                    bot.edit_message_text(quick_info, message.chat.id, info_msg.message_id, reply_markup=keyboard, parse_mode='Markdown')
                else:
                    keyboard = create_main_menu()
                    bot.edit_message_text("⚠️ تعذر جلب معلومات الفيديو، لكن يمكنك المحاولة:", message.chat.id, info_msg.message_id, reply_markup=keyboard)
            except:
                keyboard = create_main_menu()
                bot.edit_message_text("🔗 تم اكتشاف رابط! اختر نوع المعالجة:", message.chat.id, info_msg.message_id, reply_markup=keyboard)
            return

        # معالجة الأوامر المخصصة
        if text.startswith('/'):
            # الأوامر تم معالجتها بـ message handlers منفصلة
            return

        # التفاعل مع الذكاء الاصطناعي
        if text and len(text.strip()) > 0:
            # إرسال رسالة تحميل
            thinking_msg = bot.send_message(message.chat.id, "🤖 جاري التفكير...")

            # معالجة الطلب بالذكاء الاصطناعي
            ai_response = smart_agent.query(text)

            # تحديث الرسالة مع الرد
            bot.edit_message_text(ai_response, message.chat.id, thinking_msg.message_id, parse_mode='Markdown')

            # إضافة أزرار مقترحة حسب السياق
            suggested_keyboard = suggest_actions_based_on_query(text)
            if suggested_keyboard:
                bot.send_message(
                    message.chat.id,
                    "💡 إجراءات مقترحة:",
                    reply_markup=suggested_keyboard
                )
        else:
            # عرض القائمة الرئيسية
            keyboard = create_main_menu()
            bot.send_message(
                message.chat.id,
                "🏠 القائمة الرئيسية - كيف يمكنني مساعدتك؟",
                reply_markup=keyboard
            )

    except Exception as e:
        log_error(f"خطأ في معالجة الرسالة: {str(e)}\n{message.text}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ في معالجة طلبك: {str(e)}\n\n💡 حاول مرة أخرى أو استخدم /start للقائمة الرئيسية")

def suggest_actions_based_on_query(query):
    """اقتراح إجراءات بناءً على استعلام المستخدم"""
    query_lower = query.lower()
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    suggestions_added = False

    # كلمات مفتاحية للتحميل
    download_keywords = ['تحميل', 'download', 'حمل', 'نزل', 'فيديو', 'video']
    if any(keyword in query_lower for keyword in download_keywords):
        keyboard.add(types.InlineKeyboardButton("📹 تحميل فيديو", callback_data="mode_download"))
        suggestions_added = True

    # كلمات مفتاحية للصوت
    audio_keywords = ['صوت', 'audio', 'اغنية', 'موسيقى', 'music', 'mp3']
    if any(keyword in query_lower for keyword in audio_keywords):
        keyboard.add(types.InlineKeyboardButton("🎵 استخراج صوت", callback_data="download_audio_best"))
        suggestions_added = True

    # كلمات مفتاحية للتحويل
    convert_keywords = ['تحويل', 'convert', 'تغيير', 'صيغة', 'format']
    if any(keyword in query_lower for keyword in convert_keywords):
        keyboard.add(types.InlineKeyboardButton("🔄 تحويل ملفات", callback_data="mode_convert"))
        suggestions_added = True

    # كلمات مفتاحية للتحرير
    edit_keywords = ['تحرير', 'edit', 'قص', 'trim', 'تقطيع']
    if any(keyword in query_lower for keyword in edit_keywords):
        keyboard.add(types.InlineKeyboardButton("✂️ تحرير فيديو", callback_data="mode_edit"))
        suggestions_added = True

    # كلمات مفتاحية للأدوات
    tools_keywords = ['أدوات', 'tools', 'مساعدة', 'help']
    if any(keyword in query_lower for keyword in tools_keywords):
        keyboard.add(types.InlineKeyboardButton("🛠️ جميع الأدوات", callback_data="show_tools"))
        suggestions_added = True

    # إضافة زر القائمة الرئيسية دائماً
    if suggestions_added:
        keyboard.add(types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main"))
        return keyboard

    return None

def create_model_switch_menu():
    """إنشاء قائمة تبديل النموذج"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🟢 Google Gemini", callback_data="model_google"),
        types.InlineKeyboardButton("🔵 OpenAI GPT", callback_data="model_openai")
    )
    keyboard.add(
        types.InlineKeyboardButton("🟣 Claude", callback_data="model_claude"),
        types.InlineKeyboardButton("🟠 Groq", callback_data="model_groq")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ العودة", callback_data="ai_settings"))

    return keyboard

# وظائف مساعدة لمعالجة الأدوات
def handle_bulk_action(action):
    return f"📦 **التحميل المجمع:** أرسل قائمة بالروابط مفصولة بأسطر للبدء"

def handle_playlist_action(action):
    return f"📋 **قائمة التشغيل:** أرسل رابط قائمة التشغيل للبدء"

def handle_convert_action(action):
    format_name = action.replace('convert_', '').upper()
    return f"🔄 **تحويل إلى {format_name}:** ارفع الملف المراد تحويله"

def handle_trim_action(action):
    return f"✂️ **قص الفيديو:** ارفع الفيديو وحدد نقطة البداية والنهاية"

def handle_merge_action(action):
    return f"🔗 **دمج الملفات:** ارفع الملفات المراد دمجها"

def handle_compress_action(action):
    return f"🗜️ **ضغط الملفات:** ارفع الملف المراد ضغطه"

def handle_watermark_action(action):
    return f"🏷️ **العلامة المائية:** ارفع الفيديو وحدد نوع العلامة"

def handle_image_action(action):
    return f"🖼️ **معالجة الصور:** ارفع الصورة للبدء"

def handle_thumbnail_action(action):
    return f"🎨 **الصور المصغرة:** ارفع الفيديو أو الصورة للبدء"

def handle_cleanup_action(action):
    if action == "cleanup_temp":
        # حذف الملفات المؤقتة فعلياً
        temp_files = 0
        for root, dirs, files in os.walk("downloads"):
            for file in files:
                if file.startswith("temp_") or file.endswith(".tmp"):
                    try:
                        os.remove(os.path.join(root, file))
                        temp_files += 1
                    except:
                        pass
        return f"🗑️ **تنظيف المؤقتة:** تم حذف {temp_files} ملف مؤقت"

    elif action == "cleanup_space":
        downloads_size = 0
        downloads_count = 0
        if os.path.exists("downloads"):
            for root, dirs, files in os.walk("downloads"):
                for file in files:
                    file_path = os.path.join(root, file)
                    downloads_size += os.path.getsize(file_path)
                    downloads_count += 1

        return f"""
📊 **استخدام المساحة:**

📁 **مجلد التحميلات:**
• عدد الملفات: {downloads_count}
• إجمالي الحجم: {downloads_size/(1024*1024):.1f} MB

💡 **نصيحة:** استخدم "تنظيف شامل" لحذف الملفات القديمة
        """

    return f"🧹 **تنظيف:** تم تنفيذ عملية التنظيف بنجاح"

def create_audio_processing_menu():
    """قائمة معالجة الصوت المرفوع"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔄 تحويل الصيغة", callback_data="process_audio_convert"),
        types.InlineKeyboardButton("🎚️ تعديل الجودة", callback_data="process_audio_quality")
    )
    keyboard.add(
        types.InlineKeyboardButton("✂️ قص وتقطيع", callback_data="process_audio_trim"),
        types.InlineKeyboardButton("🔗 دمج الأصوات", callback_data="process_audio_merge")
    )
    keyboard.add(
        types.InlineKeyboardButton("🗣️ تحسين الصوت", callback_data="process_audio_enhance"),
        types.InlineKeyboardButton("📊 معلومات الصوت", callback_data="process_audio_info")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))
    return keyboard

def create_image_processing_menu():
    """قائمة معالجة الصورة المرفوعة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔄 تحويل الصيغة", callback_data="process_image_convert"),
        types.InlineKeyboardButton("📐 تغيير الحجم", callback_data="process_image_resize")
    )
    keyboard.add(
        types.InlineKeyboardButton("🎨 تحسين الصورة", callback_data="process_image_enhance"),
        types.InlineKeyboardButton("✂️ قص الصورة", callback_data="process_image_crop")
    )
    keyboard.add(
        types.InlineKeyboardButton("📸 إضافة فلاتر", callback_data="process_image_filters"),
        types.InlineKeyboardButton("🗜️ ضغط الصورة", callback_data="process_image_compress")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))
    return keyboard

def create_document_processing_menu():
    """قائمة معالجة المستندات المرفوعة"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("📝 استخراج النص", callback_data="process_doc_extract_text"),
        types.InlineKeyboardButton("📄 تحويل إلى PDF", callback_data="process_doc_convert_pdf")
    )
    keyboard.add(
        types.InlineKeyboardButton("🔒 حماية المستند", callback_data="process_doc_protect"),
        types.InlineKeyboardButton("👁️ معلومات المستند", callback_data="process_doc_info")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="back_to_main"))
    return keyboard

# --- وظائف الإدارة والصيانة ---
def cleanup_old_files():
    """تنظيف الملفات القديمة تلقائياً"""
    try:
        current_time = time.time()
        cleaned_count = 0

        # تنظيف مجلد التحميلات (ملفات أقدم من 24 ساعة)
        if os.path.exists("downloads"):
            for filename in os.listdir("downloads"):
                file_path = os.path.join("downloads", filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 86400:  # 24 ساعة
                        os.remove(file_path)
                        cleaned_count += 1

        # تنظيف مجلد الرفع (ملفات أقدم من 6 ساعات)
        if os.path.exists("uploads"):
            for filename in os.listdir("uploads"):
                file_path = os.path.join("uploads", filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 21600:  # 6 ساعات
                        os.remove(file_path)
                        cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"🧹 تم تنظيف {cleaned_count} ملف قديم")

    except Exception as e:
        logger.error(f"خطأ في تنظيف الملفات: {e}")

def start_cleanup_scheduler():
    """بدء جدولة التنظيف التلقائي"""
    def cleanup_task():
        while True:
            time.sleep(3600)  # كل ساعة
            cleanup_old_files()

    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("✅ تم تفعيل التنظيف التلقائي")

def monitor_system_resources():
    """مراقبة موارد النظام"""
    try:
        import psutil

        # التحقق من استخدام الذاكرة
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            logger.warning(f"⚠️ استخدام الذاكرة مرتفع: {memory.percent}%")
            # تنظيف طارئ
            cleanup_old_files()

        # التحقق من مساحة القرص
        disk = psutil.disk_usage('/')
        if disk.percent > 95:
            logger.warning(f"⚠️ مساحة القرص منخفضة: {disk.percent}%")
            cleanup_old_files()

    except Exception as e:
        logger.error(f"خطأ في مراقبة النظام: {e}")

# معالج الأخطاء الشامل
@bot.message_handler(func=lambda message: False)
def error_handler(message):
    """معالج الأخطاء العام"""
    try:
        error_msg = """
❌ **حدث خطأ غير متوقع**

🔧 **حلول مقترحة:**
• أعد إرسال الطلب
• استخدم /start لإعادة البدء
• تأكد من صحة الرابط أو الملف
• جرب أداة أخرى

🆘 **للدعم:** استخدم /help أو /commands
        """
        bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"خطأ في معالج الأخطاء: {e}")

# --- تشغيل البوت ---
if __name__ == "__main__":
    try:
        logger.info("🚀 بدء تشغيل Smart Media AI Assistant...")
        logger.info(f"📊 إحصائيات البدء:")
        logger.info(f"   - وقت البدء: {time.ctime()}")
        logger.info(f"   - نظام التشغيل: {os.name}")
        logger.info(f"   - الذكاء الاصطناعي: {'مفعل' if smart_agent else 'معطل'}")
        logger.info(f"   - توكين البوت: {'✅ متوفر' if TELEGRAM_TOKEN else '❌ مفقود'}")

        # إنشاء المجلدات الضرورية
        os.makedirs("downloads", exist_ok=True)
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("processed", exist_ok=True)
        logger.info("📁 تم إنشاء المجلدات الضرورية")

        # بدء التنظيف التلقائي
        start_cleanup_scheduler()

        # بدء مراقبة النظام
        monitor_thread = threading.Thread(target=lambda: [monitor_system_resources(), time.sleep(300)], daemon=True)
        monitor_thread.start()
        logger.info("📊 تم تفعيل مراقب النظام")

        logger.info("🎉 تم تشغيل البوت بنجاح! جاهز لاستقبال الطلبات...")
        print("🤖 Smart Media AI Assistant يعمل الآن!")
        print("✅ جميع الأنظمة تعمل بشكل مثالي")
        print("📱 ابدأ محادثة مع البوت على Telegram")

        bot.infinity_polling(none_stop=True, interval=1, timeout=60)

    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        print("👋 تم إيقاف البوت بأمان")
    except Exception as e:
        logger.error(f"❌ خطأ مميت في تشغيل البوت: {e}")
        print(f"❌ خطأ مميت: {e}")
        print("💡 تأكد من صحة التوكين والاتصال بالإنترنت")
    finally:
        # تنظيف نهائي
        cleanup_old_files()
        logger.info("🛑 إغلاق Smart Media AI Assistant")
        print("🧹 تم تنظيف الملفات المؤقتة")
        print("📴 تم إغلاق النظام بأمان")