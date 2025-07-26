
"""
config_manager.py - مدير الإعدادات المحسن
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class BotConfig:
    """إعدادات البوت"""
    telegram_token: str
    max_file_size_mb: int = 100
    max_requests_per_minute: int = 20
    supported_formats: list = None
    default_quality: str = "best"
    enable_ai: bool = True
    enable_performance_monitoring: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.mp4', '.mp3', '.avi', '.mkv', '.wav', '.m4a', '.webm']

@dataclass 
class AIConfig:
    """إعدادات الذكاء الاصطناعي"""
    default_provider: str = "google"
    default_model: str = "gemini-2.0-flash"
    max_context_length: int = 4000
    temperature: float = 0.7
    enable_memory: bool = True
    memory_window_size: int = 10

class ConfigManager:
    """مدير الإعدادات المتقدم"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self._bot_config: Optional[BotConfig] = None
        self._ai_config: Optional[AIConfig] = None
        
    def load_config(self) -> BotConfig:
        """تحميل الإعدادات"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # تحميل إعدادات البوت
                bot_data = {
                    'telegram_token': data.get('TELEGRAM_TOKEN', ''),
                    'max_file_size_mb': data.get('MAX_FILE_SIZE_MB', 100),
                    'max_requests_per_minute': data.get('MAX_REQUESTS_PER_MINUTE', 20),
                    'supported_formats': data.get('SUPPORTED_FORMATS'),
                    'default_quality': data.get('DEFAULT_QUALITY', 'best'),
                    'enable_ai': data.get('ENABLE_AI', True),
                    'enable_performance_monitoring': data.get('ENABLE_PERFORMANCE_MONITORING', True),
                    'log_level': data.get('LOG_LEVEL', 'INFO')
                }
                
                self._bot_config = BotConfig(**bot_data)
                
                # تحميل إعدادات AI
                ai_data = data.get('AI_CONFIG', {})
                self._ai_config = AIConfig(**ai_data)
                
                self.logger.info("✅ تم تحميل الإعدادات بنجاح")
                return self._bot_config
                
            else:
                # إنشاء إعدادات افتراضية
                self.logger.warning(f"⚠️ ملف {self.config_file} غير موجود، سيتم إنشاء إعدادات افتراضية")
                return self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحميل الإعدادات: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> BotConfig:
        """إنشاء إعدادات افتراضية"""
        self._bot_config = BotConfig(telegram_token="")
        self._ai_config = AIConfig()
        
        # حفظ الإعدادات الافتراضية
        self.save_config()
        return self._bot_config
    
    def save_config(self):
        """حفظ الإعدادات"""
        try:
            config_data = {}
            
            if self._bot_config:
                config_data.update({
                    'TELEGRAM_TOKEN': self._bot_config.telegram_token,
                    'MAX_FILE_SIZE_MB': self._bot_config.max_file_size_mb,
                    'MAX_REQUESTS_PER_MINUTE': self._bot_config.max_requests_per_minute,
                    'SUPPORTED_FORMATS': self._bot_config.supported_formats,
                    'DEFAULT_QUALITY': self._bot_config.default_quality,
                    'ENABLE_AI': self._bot_config.enable_ai,
                    'ENABLE_PERFORMANCE_MONITORING': self._bot_config.enable_performance_monitoring,
                    'LOG_LEVEL': self._bot_config.log_level
                })
            
            if self._ai_config:
                config_data['AI_CONFIG'] = asdict(self._ai_config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("✅ تم حفظ الإعدادات بنجاح")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ الإعدادات: {e}")
    
    def get_bot_config(self) -> BotConfig:
        """الحصول على إعدادات البوت"""
        if not self._bot_config:
            self.load_config()
        return self._bot_config
    
    def get_ai_config(self) -> AIConfig:
        """الحصول على إعدادات AI"""
        if not self._ai_config:
            self.load_config()
        return self._ai_config
    
    def update_bot_config(self, **kwargs):
        """تحديث إعدادات البوت"""
        if not self._bot_config:
            self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(self._bot_config, key):
                setattr(self._bot_config, key, value)
        
        self.save_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """التحقق من صحة الإعدادات"""
        issues = []
        
        if not self._bot_config:
            self.load_config()
        
        # فحص توكين التيليجرام
        if not self._bot_config.telegram_token:
            issues.append("توكين التيليجرام مفقود")
        elif len(self._bot_config.telegram_token) < 10:
            issues.append("توكين التيليجرام غير صحيح")
        
        # فحص حد حجم الملف
        if self._bot_config.max_file_size_mb <= 0 or self._bot_config.max_file_size_mb > 2000:
            issues.append("حد حجم الملف غير معقول")
        
        # فحص حد الطلبات
        if self._bot_config.max_requests_per_minute <= 0 or self._bot_config.max_requests_per_minute > 1000:
            issues.append("حد الطلبات في الدقيقة غير معقول")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'config': asdict(self._bot_config) if self._bot_config else None
        }

# مثيل وحيد
config_manager = ConfigManager()
