
# yt_dlp_wrapper.py - مغلف متطور ومحسن لـ yt-dlp
import os
import json
from typing import Dict, List, Any, Optional
import re
import logging

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("⚠️ yt-dlp غير متاح. سيتم العمل في الوضع المحاكي.")

class AdvancedMediaDownloader:
    def __init__(self):
        """تهيئة منزل الوسائط المتطور"""
        self.supported_sites = [
            'youtube', 'youtu.be', 'tiktok', 'instagram', 'twitter', 'x.com',
            'vimeo', 'facebook', 'dailymotion', 'twitch', 'reddit', 'soundcloud',
            'linkedin', 'pinterest', 'snapchat', 'whatsapp', 'telegram'
        ]
        
        # إعداد التسجيل
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_available_formats(self, url: str) -> Dict[str, Any]:
        """الحصول على جميع الصيغ المتاحة للفيديو"""
        try:
            if not YT_DLP_AVAILABLE:
                return self._mock_formats()
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'listformats': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                # تنظيم الصيغ
                video_formats = []
                audio_formats = []
                combined_formats = []
                
                for f in formats:
                    format_info = {
                        'format_id': f.get('format_id'),
                        'quality': f.get('format_note', 'غير معروف'),
                        'resolution': f.get('resolution', 'غير معروف'),
                        'fps': f.get('fps'),
                        'filesize': f.get('filesize'),
                        'filesize_mb': round(f.get('filesize', 0) / (1024*1024), 1) if f.get('filesize') else None,
                        'ext': f.get('ext'),
                        'vcodec': f.get('vcodec'),
                        'acodec': f.get('acodec'),
                        'abr': f.get('abr'),
                        'vbr': f.get('vbr'),
                        'protocol': f.get('protocol')
                    }
                    
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        combined_formats.append(format_info)
                    elif f.get('vcodec') != 'none':
                        video_formats.append(format_info)
                    elif f.get('acodec') != 'none':
                        audio_formats.append(format_info)
                
                return {
                    'video_only': sorted(video_formats, key=lambda x: self._quality_score(x.get('quality', '')), reverse=True),
                    'audio_only': sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True),
                    'combined': sorted(combined_formats, key=lambda x: self._quality_score(x.get('quality', '')), reverse=True)
                }
                
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الصيغ: {e}")
            return {'error': str(e)}
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """استخراج معلومات تفصيلية عن الفيديو مع الصيغ المتاحة"""
        try:
            if not YT_DLP_AVAILABLE:
                return self._mock_video_info(url)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractflat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # الحصول على الصيغ المتاحة
                available_formats = self.get_available_formats(url)
                
                # تنظيم المعلومات
                processed_info = {
                    'title': info.get('title', 'غير متاح'),
                    'uploader': info.get('uploader', 'غير متاح'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'غير متاح'),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else 'غير متاح',
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url'),
                    'extractor': info.get('extractor'),
                    'platform': self._detect_platform(url),
                    'available_formats': available_formats,
                    'best_video_format': self._get_best_format(available_formats.get('combined', []), 'video'),
                    'best_audio_format': self._get_best_format(available_formats.get('audio_only', []), 'audio')
                }
                
                return processed_info
                
        except Exception as e:
            self.logger.error(f"خطأ في استخراج المعلومات: {e}")
            return {'error': f"خطأ في استخراج المعلومات: {str(e)}"}
    
    def download_with_format_id(self, url: str, format_id: str, output_dir: str = "downloads") -> Dict[str, Any]:
        """تحميل باستخدام معرف صيغة محدد"""
        try:
            if not YT_DLP_AVAILABLE:
                return self._mock_download_result("video")
            
            os.makedirs(output_dir, exist_ok=True)
            
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': format_id,
                'writeinfojson': False,
                'writesubtitles': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                return {
                    'success': True,
                    'filename': os.path.basename(filename),
                    'filepath': filename,
                    'title': info.get('title', 'غير متاح'),
                    'filesize_mb': round(os.path.getsize(filename) / (1024*1024), 1) if os.path.exists(filename) else None,
                    'format_id': format_id
                }
                
        except Exception as e:
            self.logger.error(f"خطأ في التحميل: {e}")
            return {
                'success': False,
                'error': f"خطأ في تحميل الفيديو: {str(e)}"
            }
    
    def download_video(self, url: str, output_dir: str = "downloads", quality: str = "best") -> Dict[str, Any]:
        """تحميل فيديو بجودة محددة مع معالجة أخطاء محسنة"""
        try:
            if not YT_DLP_AVAILABLE:
                return self._mock_download_result("video")
            
            os.makedirs(output_dir, exist_ok=True)
            
            # الحصول على الصيغ المتاحة أولاً
            formats_info = self.get_available_formats(url)
            if 'error' in formats_info:
                return {'success': False, 'error': formats_info['error']}
            
            # اختيار أفضل صيغة متاحة
            best_format = self._select_best_available_format(formats_info, quality)
            
            if not best_format:
                return {
                    'success': False,
                    'error': f"لا توجد صيغة متاحة للجودة المطلوبة: {quality}"
                }
            
            return self.download_with_format_id(url, best_format['format_id'], output_dir)
                
        except Exception as e:
            self.logger.error(f"خطأ في التحميل: {e}")
            return {
                'success': False,
                'error': f"خطأ في تحميل الفيديو: {str(e)}"
            }
    
    def download_audio(self, url: str, output_dir: str = "downloads", quality: str = "best") -> Dict[str, Any]:
        """تحميل الصوت فقط مع معالجة أخطاء محسنة"""
        try:
            if not YT_DLP_AVAILABLE:
                return self._mock_download_result("audio")
            
            os.makedirs(output_dir, exist_ok=True)
            
            # تحديد جودة الصوت
            audio_quality = {
                'best': '0',
                'high': '192',
                'medium': '128',
                'low': '96'
            }.get(quality, '192')
            
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }],
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # البحث عن الملف المحول
                base_filename = ydl.prepare_filename(info)
                audio_filename = os.path.splitext(base_filename)[0] + '.mp3'
                
                return {
                    'success': True,
                    'filename': os.path.basename(audio_filename),
                    'filepath': audio_filename,
                    'title': info.get('title', 'غير متاح'),
                    'filesize_mb': round(os.path.getsize(audio_filename) / (1024*1024), 1) if os.path.exists(audio_filename) else None,
                    'quality': f'{audio_quality}kbps'
                }
                
        except Exception as e:
            self.logger.error(f"خطأ في استخراج الصوت: {e}")
            return {
                'success': False,
                'error': f"خطأ في استخراج الصوت: {str(e)}"
            }
    
    def _select_best_available_format(self, formats_info: Dict, quality: str) -> Optional[Dict]:
        """اختيار أفضل صيغة متاحة حسب الجودة المطلوبة"""
        combined = formats_info.get('combined', [])
        video_only = formats_info.get('video_only', [])
        
        # أولوية للصيغ المدمجة
        all_formats = combined + video_only
        
        if not all_formats:
            return None
        
        # خريطة الجودات
        quality_map = {
            'best': 99999,
            '4k': 2160,
            '2160': 2160,
            '1440': 1440,
            '1080': 1080,
            '720': 720,
            '480': 480,
            '360': 360,
            '240': 240
        }
        
        target_quality = quality_map.get(quality, 720)
        
        # البحث عن أقرب جودة متاحة
        best_match = None
        best_score = float('inf')
        
        for fmt in all_formats:
            fmt_quality = self._quality_score(fmt.get('quality', ''))
            score = abs(fmt_quality - target_quality)
            
            if score < best_score:
                best_score = score
                best_match = fmt
        
        return best_match
    
    def _detect_platform(self, url: str) -> str:
        """اكتشاف المنصة من الرابط"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'YouTube'
        elif 'tiktok.com' in url:
            return 'TikTok'
        elif 'instagram.com' in url:
            return 'Instagram'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'Twitter/X'
        elif 'facebook.com' in url:
            return 'Facebook'
        elif 'vimeo.com' in url:
            return 'Vimeo'
        else:
            return 'منصة أخرى'
    
    def _get_best_format(self, formats: List[Dict], type: str) -> Optional[Dict]:
        """الحصول على أفضل صيغة من نوع معين"""
        if not formats:
            return None
        
        if type == 'video':
            return max(formats, key=lambda x: self._quality_score(x.get('quality', '')))
        elif type == 'audio':
            return max(formats, key=lambda x: x.get('abr', 0))
        
        return formats[0]
    
    def _quality_score(self, quality: str) -> int:
        """تقييم الجودة لترتيبها"""
        quality_str = str(quality).lower()
        if '4k' in quality_str or '2160' in quality_str:
            return 2160
        elif '1440' in quality_str:
            return 1440
        elif '1080' in quality_str:
            return 1080
        elif '720' in quality_str:
            return 720
        elif '480' in quality_str:
            return 480
        elif '360' in quality_str:
            return 360
        elif '240' in quality_str:
            return 240
        else:
            # محاولة استخراج رقم من النص
            numbers = re.findall(r'\d+', quality_str)
            return int(numbers[0]) if numbers else 0
    
    def _mock_formats(self) -> Dict[str, List]:
        """صيغ وهمية للاختبار"""
        return {
            'combined': [
                {'format_id': '22', 'quality': '720p', 'resolution': '1280x720', 'filesize_mb': 25.5, 'ext': 'mp4'},
                {'format_id': '18', 'quality': '360p', 'resolution': '640x360', 'filesize_mb': 15.2, 'ext': 'mp4'}
            ],
            'video_only': [
                {'format_id': '137', 'quality': '1080p', 'resolution': '1920x1080', 'filesize_mb': 45.0, 'ext': 'mp4'},
                {'format_id': '136', 'quality': '720p', 'resolution': '1280x720', 'filesize_mb': 30.0, 'ext': 'mp4'}
            ],
            'audio_only': [
                {'format_id': '140', 'quality': '128kbps', 'abr': 128, 'filesize_mb': 3.5, 'ext': 'm4a'},
                {'format_id': '139', 'quality': '48kbps', 'abr': 48, 'filesize_mb': 1.5, 'ext': 'm4a'}
            ]
        }
    
    def _mock_video_info(self, url: str) -> Dict[str, Any]:
        """معلومات وهمية للاختبار"""
        return {
            'title': 'فيديو تجريبي - Smart Media Assistant',
            'uploader': 'قناة تجريبية',
            'duration': 180,
            'view_count': 1000,
            'upload_date': '20240101',
            'description': 'هذا فيديو تجريبي لاختبار النظام...',
            'thumbnail': None,
            'platform': 'YouTube',
            'available_formats': self._mock_formats()
        }
    
    def _mock_download_result(self, type: str) -> Dict[str, Any]:
        """نتيجة تحميل وهمية للاختبار"""
        if type == "audio":
            return {
                'success': True,
                'filename': 'test_audio.mp3',
                'filepath': 'downloads/test_audio.mp3',
                'title': 'صوت تجريبي',
                'filesize_mb': 3.5
            }
        else:
            return {
                'success': True,
                'filename': 'test_video.mp4',
                'filepath': 'downloads/test_video.mp4',
                'title': 'فيديو تجريبي',
                'filesize_mb': 25.5
            }

# إنشاء مثيل وحيد
downloader = AdvancedMediaDownloader()

# دوال للتوافق مع الكود القديم
def get_video_info(url: str) -> str:
    """دالة للتوافق مع الكود القديم"""
    info = downloader.get_video_info(url)
    
    if 'error' in info:
        return f"❌ {info['error']}"
    
    duration = info['duration']
    minutes = duration // 60
    seconds = duration % 60
    
    formats = info.get('available_formats', {})
    combined_formats = formats.get('combined', [])
    
    result = f"""
🎬 **معلومات الفيديو:**

📝 العنوان: {info['title']}
👤 القناة: {info['uploader']}
⏱️ المدة: {minutes:02d}:{seconds:02d}
👁️ المشاهدات: {info['view_count']}
🌐 المنصة: {info.get('platform', 'غير معروف')}

🎯 الجودات المتاحة:
"""
    
    for fmt in combined_formats[:5]:
        result += f"📹 {fmt.get('quality')} - {fmt.get('filesize_mb', 'غير معروف')} MB\n"
    
    return result
