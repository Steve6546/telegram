# -*- coding: utf-8 -*-
"""
This module contains all the message and callback handlers for the bot.
يحتوي هذا الملف على جميع معالجات الرسائل والأزرار الخاصة بالبوت.
"""
import time
import psutil
from datetime import datetime
from telebot import types

# Import local modules
from .ai_agent import smart_agent
from . import keyboards
from . import utils
from .main import bot, user_states, get_completed_operations, count_downloaded_files, start_time, handle_download_request, log_error

def register_handlers():
    """Register all handlers for the bot."""

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """رسالة ترحيبية متطورة"""
        welcome_text = f"🚀 **مرحباً {message.from_user.first_name}!**\nأنا **Smart Media AI Assistant** - مساعدك الذكي المتطور."
        keyboard = keyboards.create_main_menu()
        bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode='Markdown')

    @bot.message_handler(commands=['status', 'حالة'])
    def show_status(message):
        """عرض حالة النظام"""
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
    ✅ **الحالة:** نشط ويعمل بشكل مثالي!
        """
        bot.send_message(message.chat.id, status_text, parse_mode='Markdown')

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        """معالجة جميع الرسائل النصية"""
        try:
            user_id = message.from_user.id
            text = message.text if message.text else ""
            url = utils.extract_url(text)

            if url:
                user_states[user_id] = {'url': url}
                info_msg = bot.send_message(message.chat.id, "🔍 جاري فحص الرابط...")
                keyboard = keyboards.create_dynamic_download_options(url)
                bot.edit_message_text("اختر خيارات التحميل:", message.chat.id, info_msg.message_id, reply_markup=keyboard)
            else:
                thinking_msg = bot.send_message(message.chat.id, "🤖 جاري التفكير...")
                ai_response = smart_agent.query(text)
                bot.edit_message_text(ai_response, message.chat.id, thinking_msg.message_id, parse_mode='Markdown')
                suggested_keyboard = utils.suggest_actions_based_on_query(text)
                if suggested_keyboard:
                    bot.send_message(message.chat.id, "💡 إجراءات مقترحة:", reply_markup=suggested_keyboard)

        except Exception as e:
            log_error(f"خطأ في معالجة الرسالة: {str(e)}\n{message.text}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ في معالجة طلبك.")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        """معالجة جميع الأزرار التفاعلية"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data = call.data
        bot.answer_callback_query(call.id)

        if data == "back_to_main":
            keyboard = keyboards.create_main_menu()
            bot.edit_message_text("🏠 القائمة الرئيسية - اختر الخدمة المطلوبة:", chat_id, call.message.message_id, reply_markup=keyboard)
        
        elif data.startswith("download_") and user_id in user_states and 'url' in user_states[user_id]:
            url = user_states[user_id]['url']
            handle_download_request(chat_id, user_id, url, data)
        
        else:
            bot.answer_callback_query(call.id, f"⚠️ الوظيفة {data} قيد التطوير")