
"""
tests.py - نظام اختبارات شامل للمشروع
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append('.')

from yt_dlp_wrapper import AdvancedMediaDownloader
from ai_agent import SmartMediaAgent, MultiModelAIManager
from performance_monitor import PerformanceMonitor

class TestAdvancedMediaDownloader(unittest.TestCase):
    """اختبارات منزل الوسائط"""
    
    def setUp(self):
        self.downloader = AdvancedMediaDownloader()
        self.test_url = "https://youtube.com/watch?v=test123"
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_detect_platform(self):
        """اختبار اكتشاف المنصة"""
        test_cases = [
            ("https://youtube.com/watch?v=123", "YouTube"),
            ("https://tiktok.com/@user/video/123", "TikTok"),
            ("https://instagram.com/p/123", "Instagram"),
            ("https://twitter.com/user/status/123", "Twitter/X"),
            ("https://example.com/video", "منصة أخرى")
        ]
        
        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.downloader._detect_platform(url)
                self.assertEqual(result, expected)
    
    def test_quality_score(self):
        """اختبار تقييم الجودة"""
        test_cases = [
            ("1080p", 1080),
            ("720p HD", 720),
            ("4K", 2160),
            ("360p", 360),
            ("unknown", 0)
        ]
        
        for quality, expected in test_cases:
            with self.subTest(quality=quality):
                result = self.downloader._quality_score(quality)
                self.assertEqual(result, expected)
    
    @patch('yt_dlp.YoutubeDL')
    def test_get_video_info_success(self, mock_ydl):
        """اختبار استخراج معلومات الفيديو بنجاح"""
        mock_instance = Mock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        mock_info = {
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'duration': 180,
            'view_count': 1000,
            'upload_date': '20240101'
        }
        mock_instance.extract_info.return_value = mock_info
        
        result = self.downloader.get_video_info(self.test_url)
        
        self.assertEqual(result['title'], 'Test Video')
        self.assertEqual(result['uploader'], 'Test Channel')
        self.assertEqual(result['duration'], 180)

class TestMultiModelAIManager(unittest.TestCase):
    """اختبارات مدير النماذج المتعددة"""
    
    def setUp(self):
        self.manager = MultiModelAIManager()
    
    def test_available_providers(self):
        """اختبار الموفرين المتاحين"""
        providers = self.manager.get_available_providers()
        self.assertIsInstance(providers, dict)
        
        expected_providers = ['openai', 'google', 'openrouter', 'anthropic']
        for provider in expected_providers:
            self.assertIn(provider, self.manager.available_models)
    
    def test_set_active_model_invalid_provider(self):
        """اختبار تعيين موفر غير صحيح"""
        result = self.manager.set_active_model("invalid_provider", "test_model")
        self.assertFalse(result['success'])
        self.assertIn('موفر غير مدعوم', result['error'])
    
    def test_set_active_model_invalid_model(self):
        """اختبار تعيين نموذج غير صحيح"""
        result = self.manager.set_active_model("openai", "invalid_model")
        self.assertFalse(result['success'])
        self.assertIn('نموذج غير مدعوم', result['error'])

class TestPerformanceMonitor(unittest.TestCase):
    """اختبارات مراقب الأداء"""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    def test_record_operation(self):
        """اختبار تسجيل العمليات"""
        initial_count = len(self.monitor.operation_times)
        
        self.monitor.record_operation(1.5)
        self.assertEqual(len(self.monitor.operation_times), initial_count + 1)
        self.assertEqual(self.monitor.operation_times[-1], 1.5)
    
    def test_record_error(self):
        """اختبار تسجيل الأخطاء"""
        initial_count = self.monitor.error_count
        
        self.monitor.record_error()
        self.assertEqual(self.monitor.error_count, initial_count + 1)
    
    def test_get_real_time_stats(self):
        """اختبار الإحصائيات الفورية"""
        stats = self.monitor.get_real_time_stats()
        
        required_keys = [
            'cpu_percent', 'memory_percent', 'memory_available_gb',
            'active_operations', 'total_errors', 'avg_response_time'
        ]
        
        for key in required_keys:
            self.assertIn(key, stats)
            self.assertIsInstance(stats[key], (int, float))

class TestIntegration(unittest.TestCase):
    """اختبارات التكامل الشاملة"""
    
    def setUp(self):
        self.downloader = AdvancedMediaDownloader()
        self.monitor = PerformanceMonitor()
    
    def test_full_workflow_simulation(self):
        """اختبار محاكاة سير العمل الكامل"""
        # محاكاة طلب تحميل
        test_url = "https://youtube.com/watch?v=test123"
        
        # فحص الرابط
        platform = self.downloader._detect_platform(test_url)
        self.assertEqual(platform, "YouTube")
        
        # محاكاة تسجيل عملية
        start_time = 0
        end_time = 2.5
        operation_duration = end_time - start_time
        
        self.monitor.record_operation(operation_duration)
        
        # التحقق من التسجيل
        self.assertGreater(len(self.monitor.operation_times), 0)
        self.assertEqual(self.monitor.operation_times[-1], operation_duration)
    
    def test_error_handling_workflow(self):
        """اختبار سير العمل عند الأخطاء"""
        initial_errors = self.monitor.error_count
        
        # محاكاة خطأ
        self.monitor.record_error()
        
        # التحقق من تسجيل الخطأ
        self.assertEqual(self.monitor.error_count, initial_errors + 1)

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("🧪 بدء تشغيل الاختبارات الشاملة...")
    
    # إنشاء مجموعة الاختبارات
    test_suite = unittest.TestSuite()
    
    # إضافة اختبارات الوحدة
    test_classes = [
        TestAdvancedMediaDownloader,
        TestMultiModelAIManager,
        TestPerformanceMonitor,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # تقرير النتائج
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"""
📊 **نتائج الاختبارات:**

✅ **المجموع:** {total_tests}
❌ **الفشل:** {failures}
🚫 **الأخطاء:** {errors}
📈 **معدل النجاح:** {success_rate:.1f}%

{'🎉 جميع الاختبارات نجحت!' if failures == 0 and errors == 0 else '⚠️ هناك اختبارات فاشلة تحتاج إصلاح'}
    """)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_all_tests()
