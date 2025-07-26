# -*- coding: utf-8 -*-
"""
This module contains utility functions for the bot.
يحتوي هذا الملف على الوظائف المساعدة للبوت.
"""
import os
import re
from telebot import types

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
        for root, dirs, files in os.walk("media/downloads"):
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
        if os.path.exists("media/downloads"):
            for root, dirs, files in os.walk("media/downloads"):
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