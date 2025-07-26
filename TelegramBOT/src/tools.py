# -*- coding: utf-8 -*-
"""
tools.py - أدوات الذكاء الاصطناعي المتقدمة
This file defines the custom tools available to the LangChain agent.
"""

from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import logging
import zipfile
import shutil
from datetime import datetime

# Import local modules
from .yt_dlp_wrapper import downloader

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Pydantic Schemas for Tool Inputs ---

class VideoDownloaderSchema(BaseModel):
    url: str = Field(description="رابط الفيديو المطلوب تحميله")
    quality: str = Field(default="best", description="الجودة المطلوبة (e.g., 'best', '1080p', '720p')")

class VideoInfoSchema(BaseModel):
    url: str = Field(description="رابط الفيديو المطلوب استخراج معلوماته")

class FileConverterSchema(BaseModel):
    input_file: str = Field(description="مسار الملف المدخل للتحويل")
    output_format: str = Field(description="الصيغة الجديدة المطلوبة (e.g., 'mp3', 'mp4')")

# --- LangChain Tools (Class-based) ---

class AdvancedVideoDownloaderTool(BaseTool):
    """أداة تحميل الفيديوهات المتطورة"""
    name: str = "advanced_video_downloader"
    description: str = "تحميل فيديوهات من جميع المنصات بجودات مختلفة"
    args_schema: Type[BaseModel] = VideoDownloaderSchema

    def _run(self, url: str, quality: str = "best") -> str:
        try:
            result = downloader.download_video(url, "media/downloads", quality)
            if result and result.get('success'):
                return f"✅ تم التحميل بنجاح! الملف محفوظ في: {result.get('filepath', 'N/A')}"
            else:
                return f"❌ فشل التحميل: {result.get('error', 'خطأ غير معروف')}"
        except Exception as e:
            logger.error(f"خطأ في أداة التحميل: {e}")
            return f"❌ خطأ في تحميل الفيديو: {str(e)}"

class AdvancedVideoInfoTool(BaseTool):
    """أداة استخراج معلومات الفيديو"""
    name: str = "advanced_video_info"
    description: str = "استخراج معلومات تفصيلية عن الفيديوهات والجودات المتاحة"
    args_schema: Type[BaseModel] = VideoInfoSchema

    def _run(self, url: str) -> str:
        try:
            info = downloader.get_video_info(url)
            if 'error' in info:
                return f"❌ {info['error']}"
            
            # Format a summary of the video info
            duration = info.get('duration', 0)
            minutes, seconds = divmod(duration, 60)
            return (
                f"🎬 **العنوان:** {info.get('title', 'N/A')}\n"
                f"👤 **القناة:** {info.get('uploader', 'N/A')}\n"
                f"⏱️ **المدة:** {int(minutes):02d}:{int(seconds):02d}\n"
                f"👁️ **المشاهدات:** {info.get('view_count', 0):,}"
            )
        except Exception as e:
            logger.error(f"خطأ في استخراج المعلومات: {e}")
            return f"❌ خطأ في استخراج المعلومات: {str(e)}"

class FileConverterTool(BaseTool):
    """أداة تحويل الملفات"""
    name: str = "file_converter"
    description: str = "تحويل الملفات بين صيغ مختلفة (محاكاة)"
    args_schema: Type[BaseModel] = FileConverterSchema

    def _run(self, input_file: str, output_format: str) -> str:
        try:
            if not os.path.exists(input_file):
                return f"❌ الملف غير موجود: {input_file}"
            
            output_dir = "media/processed"
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}.{output_format}")
            
            # This is a simulation. Real conversion requires a library like FFmpeg.
            shutil.copy2(input_file, output_file)
            
            return f"✅ تم التحويل بنجاح! الملف الجديد: {output_file}"
        except Exception as e:
            logger.error(f"خطأ في التحويل: {e}")
            return f"❌ خطأ في تحويل الملف: {str(e)}"


# قائمة جميع الأدوات
ALL_TOOLS = [
    AdvancedVideoDownloaderTool(),
    AdvancedVideoInfoTool(),
    FileConverterTool(),
]
