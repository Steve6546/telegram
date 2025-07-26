
# ai_agent.py - وكيل الذكاء الاصطناعي المتطور
import os
import json
import requests
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from tools import ALL_TOOLS
from dotenv import load_dotenv

load_dotenv()

class MultiModelAIManager:
    """مدير النماذج المتعددة للذكاء الاصطناعي"""
    
    def __init__(self):
        self.available_models = {
            'openai': {
                'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
                'api_key_env': 'OPENAI_API_KEY',
                'base_url': 'https://api.openai.com/v1'
            },
            'google': {
                'models': ['gemini-2.0-flash', 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite'],
                'api_key_env': 'GEMINI_API_KEY',
                'base_url': 'https://generativelanguage.googleapis.com/v1beta'
            },
            'openrouter': {
                'models': ['claude-3-opus', 'llama-2-70b', 'mistral-7b'],
                'api_key_env': 'OPENROUTER_API_KEY',
                'base_url': 'https://openrouter.ai/api/v1'
            },
            'anthropic': {
                'models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
                'api_key_env': 'ANTHROPIC_API_KEY',
                'base_url': 'https://api.anthropic.com/v1'
            }
        }
        
        self.active_model = None
        self.active_provider = None
    
    def get_available_providers(self) -> Dict[str, List[str]]:
        """الحصول على الموفرين والنماذج المتاحة"""
        available = {}
        for provider, config in self.available_models.items():
            api_key = os.getenv(config['api_key_env'])
            if api_key:
                available[provider] = config['models']
        return available
    
    def set_active_model(self, provider: str, model: str) -> Dict[str, Any]:
        """تعيين النموذج النشط"""
        if provider not in self.available_models:
            return {'success': False, 'error': f'موفر غير مدعوم: {provider}'}
        
        config = self.available_models[provider]
        api_key = os.getenv(config['api_key_env'])
        
        if not api_key:
            return {'success': False, 'error': f'مفتاح API غير موجود لـ {provider}'}
        
        if model not in config['models']:
            return {'success': False, 'error': f'نموذج غير مدعوم: {model}'}
        
        self.active_provider = provider
        self.active_model = model
        
        return {'success': True, 'message': f'تم تعيين النموذج: {provider}/{model}'}
    
    def create_llm_instance(self):
        """إنشاء مثيل LLM حسب النموذج المختار"""
        if not self.active_provider or not self.active_model:
            return None
        
        config = self.available_models[self.active_provider]
        api_key = os.getenv(config['api_key_env'])
        
        if self.active_provider == 'google':
            return self._create_gemini_instance(api_key)
        else:
            return ChatOpenAI(
                model=self.active_model,
                openai_api_key=api_key,
                openai_api_base=config['base_url'],
                temperature=0.7
            )
    
    def _create_gemini_instance(self, api_key: str):
        """إنشاء مثيل Gemini مخصص"""
        class GeminiWrapper:
            def __init__(self, api_key: str, model: str):
                self.api_key = api_key
                self.model = model
                self.base_url = "https://generativelanguage.googleapis.com/v1beta"
            
            def invoke(self, messages):
                """استدعاء Gemini API"""
                try:
                    # تحويل الرسائل إلى صيغة Gemini
                    content = []
                    for msg in messages:
                        if hasattr(msg, 'content'):
                            content.append({"parts": [{"text": msg.content}]})
                        else:
                            content.append({"parts": [{"text": str(msg)}]})
                    
                    payload = {"contents": content}
                    
                    response = requests.post(
                        f"{self.base_url}/models/{self.model}:generateContent",
                        headers={
                            'Content-Type': 'application/json',
                            'X-goog-api-key': self.api_key
                        },
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                        return type('Response', (), {'content': text})()
                    else:
                        return type('Response', (), {'content': f'خطأ في Gemini API: {response.text}'})()
                
                except Exception as e:
                    return type('Response', (), {'content': f'خطأ في الاتصال بـ Gemini: {str(e)}'})()
        
        return GeminiWrapper(api_key, self.active_model)

class SmartMediaAgent:
    def __init__(self):
        """تهيئة وكيل الذكاء الاصطناعي المتطور"""
        self.model_manager = MultiModelAIManager()
        
        # تجريب تعيين نموذج افتراضي
        self._setup_default_model()
        
        # إعداد نموذج الذكاء الاصطناعي
        self.llm = self.model_manager.create_llm_instance()
        
        # إعداد الذاكرة (محدث للنسخة الجديدة)
        from langchain_community.chat_message_histories import ChatMessageHistory
        from langchain_core.runnables.history import RunnableWithMessageHistory
        
        self.memory = ChatMessageHistory()
        self.memory_key = "chat_history"
        
        # إعداد القالب
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # إنشاء الوكيل
        if self.llm:
            agent = create_openai_tools_agent(self.llm, ALL_TOOLS, self.prompt)
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=ALL_TOOLS,
                verbose=True,
                handle_parsing_errors=True
            )
        else:
            self.agent_executor = None
    
    def _get_system_prompt(self):
        """الحصول على تعليمات النظام"""
        return """
أنت Smart Media AI Assistant - وكيل ذكاء اصطناعي محترف ومتطور في تيليجرام.

🎯 **مهمتك الأساسية:**
- مساعدة المستخدمين في تحميل وتحويل ومعالجة الوسائط
- التفاعل بطريقة ذكية وودية ومحترفة
- استخدام الأدوات المتاحة لتنفيذ طلبات المستخدمين

🛠️ **الأدوات المتاحة لك:**
1. advanced_video_downloader - تحميل فيديوهات بجودات مختلفة
2. advanced_video_info - استخراج معلومات تفصيلية عن الفيديوهات  
3. file_converter - تحويل بين صيغ مختلفة
4. image_processor - معالجة وتحويل الصور
5. zip_manager - ضغط وفك ضغط الملفات
6. video_editor - تقطيع وتحرير الفيديوهات

📋 **قواعد التفاعل:**
- ابدأ دائماً بفهم طلب المستخدم بدقة
- إذا كان هناك رابط، استخرج معلوماته أولاً
- اعرض خيارات واضحة للمستخدم (جودات، صيغ، إلخ)
- استخدم الإيموجي لجعل التفاعل أكثر حيوية
- قدم تحديثات عن حالة العمليات الجارية
- اشرح للمستخدم ما تفعله خطوة بخطوة

💡 **أمثلة للتفاعل:**

عند استلام رابط:
"🔍 جاري فحص الرابط وجلب المعلومات..."
[استخدم advanced_video_info]
"📊 تم العثور على الفيديو! اختر نوع التحميل:
🎬 فيديو - جودة عالية (1080p)
📱 فيديو - جودة متوسطة (720p) 
🎵 صوت فقط (MP3)
ℹ️ معلومات مفصلة"

عند طلب تحويل:
"🔄 جاري تحويل الملف إلى الصيغة المطلوبة..."
[استخدم file_converter]
"✅ تم التحويل بنجاح! الملف جاهز للتحميل."

🚨 **تعليمات مهمة:**
- لا تحاول تنفيذ عمليات بدون استخدام الأدوات المحددة
- إذا فشلت أداة، حاول طريقة بديلة أو اشرح السبب
- احرص على إعطاء ردود مفيدة حتى في حالة الأخطاء
- تذكر تفاصيل المحادثة واستخدم الذاكرة بذكاء

🎨 **أسلوب التواصل:**
- كن ودوداً ومتفاعلاً
- استخدم الإيموجي بشكل مناسب
- اكتب بوضوح وبساطة
- قدم خيارات واضحة للمستخدم
- اشرح العمليات التقنية بطريقة مبسطة
        """
    
    def process_message(self, user_message: str, user_id: str = None) -> str:
        """معالجة رسالة المستخدم وإرجاع الرد"""
        try:
            # إضافة معرف المستخدم للسياق إذا كان متاحاً
            context = f"[المستخدم {user_id}]: {user_message}" if user_id else user_message
            
            if self.agent_executor:
                response = self.agent_executor.invoke({"input": context})
                return response["output"]
            else:
                # وضع التشغيل بدون AI (للاختبار)
                return self._fallback_response(user_message)
                
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "auth" in error_msg.lower():
                return """
❌ **مشكلة في التوثيق!**

🔧 **الحل:**
1. احصل على API key من OpenRouter.ai
2. أضفه في ملف .env
3. أو سأعمل في الوضع الأساسي

🤖 **الآن أعمل في الوضع الأساسي:**
""" + self._fallback_response(user_message)
            return f"❌ حدث خطأ في معالجة طلبك: {str(e)}\n💡 حاول مرة أخرى أو جرب صيغة مختلفة للطلب."
    
    def _fallback_response(self, message: str) -> str:
        """رد احتياطي عند عدم توفر AI"""
        import re
        
        # البحث عن روابط
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)
        
        if urls or "رابط" in message:
            return f"""
🔗 **تم اكتشاف رابط!** {urls[0] if urls else ''}

📊 **الخدمات المتاحة:**
📹 تحميل الفيديو بعدة جودات
🎵 استخراج الصوت MP3
ℹ️ الحصول على معلومات الفيديو

⚡ **الوضع الأساسي نشط** - الأدوات الأساسية متاحة
🔧 للذكاء الاصطناعي المتطور: أضف OpenRouter API key

💡 استخدم الأزرار للتحميل أو أرسل:
- "حمل فيديو عالي الجودة"
- "استخرج الصوت" 
- "معلومات الفيديو"
            """
        
        # ردود ذكية أساسية
        if any(word in message.lower() for word in ["مرحبا", "السلام", "أهلا", "hello"]):
            return """
🤖 **أهلاً وسهلاً عبود!** 

أنا Smart Media AI Assistant - مساعدك في:

📹 **تحميل الفيديوهات** من YouTube, TikTok, Instagram
🎵 **استخراج الصوت** بجودة عالية  
🔄 **تحويل الملفات** بين جميع الصيغ
✂️ **تحرير الوسائط** وقص المقاطع

🚀 أرسل رابط فيديو أو استخدم الأزرار!
            """
        
        if any(word in message.lower() for word in ["تحميل", "حمل", "download"]):
            return """
📹 **تحميل الفيديوهات المتاح!**

🎯 **المنصات المدعومة:**
▪️ YouTube - جميع الجودات
▪️ TikTok - بدون علامة مائية  
▪️ Instagram - Stories & Reels
▪️ Twitter/X - فيديوهات عالية الجودة
▪️ +1000 منصة أخرى

💡 **فقط أرسل الرابط وسأعطيك خيارات التحميل!**
            """
        
        return """
🤖 **مرحباً! أنا Smart Media AI Assistant**

🛠️ **الخدمات الأساسية متاحة:**
📹 تحميل الفيديوهات من جميع المنصات
🎵 استخراج واستخدام الصوت  
🔄 تحويل بين الصيغ المختلفة
✂️ تحرير وقص المقاطع
📊 الحصول على معلومات تفصيلية

⚡ **أرسل رابط للبدء فوراً!**
💡 أو استخدم الأزرار في القائمة
        """
    
    def get_available_tools_info(self) -> str:
        """الحصول على معلومات الأدوات المتاحة"""
        return """
🛠️ **الأدوات المتاحة في Smart Media AI Assistant:**

📹 **تحميل الوسائط:**
- تحميل فيديوهات بجودة 4K، HD، SD
- تحميل صوت بجودة عالية
- دعم +1000 منصة (YouTube، TikTok، Instagram، إلخ)

🔄 **تحويل الملفات:**
- تحويل بين جميع صيغ الفيديو والصوت
- ضغط وتحسين الجودة
- معالجة دفعية للملفات

✂️ **تحرير الوسائط:**
- قص وتقطيع الفيديوهات
- استخراج أجزاء محددة
- دمج عدة ملفات

🖼️ **معالجة الصور:**
- تحويل صيغ الصور
- تحسين الجودة
- تطبيق المرشحات

📦 **إدارة الملفات:**
- ضغط وفك ضغط الملفات
- إنشاء أرشيف ZIP
- إدارة المجلدات

🚀 **استخدم الأوامر التالية:**
/start - بدء جديد
/help - المساعدة
/tools - عرض الأدوات
/clear - مسح الذاكرة
        """
    
    def clear_memory(self) -> str:
        """مسح ذاكرة المحادثة"""
        if self.memory:
            self.memory.clear()
        return "🧹 تم مسح ذاكرة المحادثة بنجاح!"
    
    def _setup_default_model(self):
        """إعداد النموذج الافتراضي"""
        available_providers = self.model_manager.get_available_providers()
        
        # أولوية النماذج
        priority_order = [
            ('google', 'gemini-2.0-flash'),
            ('openai', 'gpt-4'),
            ('openrouter', 'claude-3-opus'),
            ('anthropic', 'claude-3-sonnet')
        ]
        
        for provider, model in priority_order:
            if provider in available_providers and model in available_providers[provider]:
                result = self.model_manager.set_active_model(provider, model)
                if result['success']:
                    print(f"✅ تم تعيين النموذج الافتراضي: {provider}/{model}")
                    return
        
        print("⚠️ لم يتم العثور على نماذج متاحة")
    
    def switch_model(self, provider: str, model: str) -> str:
        """تبديل النموذج المستخدم"""
        result = self.model_manager.set_active_model(provider, model)
        
        if result['success']:
            # إعادة إنشاء LLM والوكيل
            self.llm = self.model_manager.create_llm_instance()
            if self.llm:
                agent = create_openai_tools_agent(self.llm, ALL_TOOLS, self.prompt)
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=ALL_TOOLS,
                    verbose=True,
                    handle_parsing_errors=True
                )
            return f"✅ {result['message']}"
        else:
            return f"❌ {result['error']}"
    
    def get_model_info(self) -> str:
        """الحصول على معلومات النماذج المتاحة"""
        available = self.model_manager.get_available_providers()
        current = f"{self.model_manager.active_provider}/{self.model_manager.active_model}" if self.model_manager.active_provider else "غير محدد"
        
        info = f"""
🤖 **معلومات نماذج الذكاء الاصطناعي:**

🔹 **النموذج الحالي:** {current}

🌟 **النماذج المتاحة:**
"""
        
        for provider, models in available.items():
            info += f"\n📋 **{provider.upper()}:**\n"
            for model in models:
                status = "🟢" if (provider == self.model_manager.active_provider and model == self.model_manager.active_model) else "⚪"
                info += f"  {status} {model}\n"
        
        if not available:
            info += "\n❌ **لا توجد نماذج متاحة - أضف مفاتيح API**"
        
        info += """

💡 **لتبديل النموذج:**
أرسل: "استخدم google/gemini-2.0-flash"
أو: "بدل إلى openai/gpt-4"
        """
        
        return info
    
    def set_api_key(self, provider: str, api_key: str) -> str:
        """تعيين مفتاح API لموفر معين"""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'google': 'GEMINI_API_KEY',
            'gemini': 'GEMINI_API_KEY',
            'openrouter': 'OPENROUTER_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'claude': 'ANTHROPIC_API_KEY'
        }
        
        env_key = key_mapping.get(provider.lower())
        if not env_key:
            return f"❌ موفر غير مدعوم: {provider}"
        
        # حفظ المفتاح في متغير البيئة (مؤقتاً لهذه الجلسة)
        os.environ[env_key] = api_key
        
        # تحديث ملف .env
        try:
            env_path = '.env'
            env_lines = []
            
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # البحث عن المفتاح وتحديثه أو إضافته
            key_found = False
            for i, line in enumerate(env_lines):
                if line.startswith(f"{env_key}="):
                    env_lines[i] = f"{env_key}={api_key}\n"
                    key_found = True
                    break
            
            if not key_found:
                env_lines.append(f"{env_key}={api_key}\n")
            
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            return f"✅ تم حفظ مفتاح {provider} بنجاح! أعد تشغيل البوت لتفعيل التغييرات."
            
        except Exception as e:
            return f"❌ خطأ في حفظ المفتاح: {str(e)}"

# إنشاء مثيل وحيد من الوكيل
smart_agent = SmartMediaAgent()
