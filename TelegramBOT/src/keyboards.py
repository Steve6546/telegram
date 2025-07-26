# -*- coding: utf-8 -*-
"""
This module contains all functions for creating keyboards for the bot.
يحتوي هذا الملف على جميع الوظائف الخاصة بإنشاء لوحات المفاتيح التفاعلية للبوت.
"""

from telebot import types
from .yt_dlp_wrapper import downloader
import logging

logger = logging.getLogger(__name__)

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