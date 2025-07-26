
"""
performance_monitor.py - نظام مراقبة الأداء في الوقت الحقيقي
"""

import time
import psutil
import threading
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class PerformanceMetric:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    active_users: int
    operations_per_minute: int
    errors_count: int
    response_time_avg: float

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.operation_times: List[float] = []
        self.error_count = 0
        self.active_operations = 0
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """بدء مراقبة الأداء"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✅ تم بدء مراقبة الأداء")
    
    def stop_monitoring(self):
        """إيقاف مراقبة الأداء"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """حلقة المراقبة الرئيسية"""
        while self.monitoring:
            try:
                # جمع الإحصائيات
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # حساب متوسط وقت الاستجابة
                recent_times = self.operation_times[-60:]  # آخر 60 عملية
                avg_response_time = sum(recent_times) / len(recent_times) if recent_times else 0
                
                # إنشاء متريك جديد
                metric = PerformanceMetric(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    active_users=self.active_operations,
                    operations_per_minute=len(recent_times),
                    errors_count=self.error_count,
                    response_time_avg=avg_response_time
                )
                
                self.metrics.append(metric)
                
                # الاحتفاظ بآخر 1000 متريك فقط
                if len(self.metrics) > 1000:
                    self.metrics = self.metrics[-1000:]
                
                # تنبيهات الأداء
                self._check_performance_alerts(metric)
                
                time.sleep(60)  # مراقبة كل دقيقة
                
            except Exception as e:
                print(f"❌ خطأ في مراقبة الأداء: {e}")
                time.sleep(5)
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """فحص تنبيهات الأداء"""
        alerts = []
        
        if metric.cpu_percent > 80:
            alerts.append(f"⚠️ استخدام معالج مرتفع: {metric.cpu_percent:.1f}%")
        
        if metric.memory_percent > 85:
            alerts.append(f"⚠️ استخدام ذاكرة مرتفع: {metric.memory_percent:.1f}%")
        
        if metric.response_time_avg > 10:
            alerts.append(f"⚠️ وقت استجابة بطيء: {metric.response_time_avg:.2f}s")
        
        if metric.errors_count > 10:
            alerts.append(f"⚠️ أخطاء متعددة: {metric.errors_count}")
        
        if alerts:
            print("\n".join(alerts))
    
    def record_operation(self, duration: float):
        """تسجيل مدة عملية"""
        self.operation_times.append(duration)
        if len(self.operation_times) > 1000:
            self.operation_times = self.operation_times[-1000:]
    
    def record_error(self):
        """تسجيل خطأ"""
        self.error_count += 1
    
    def get_performance_report(self) -> str:
        """الحصول على تقرير الأداء"""
        if not self.metrics:
            return "📊 لا توجد بيانات أداء متاحة"
        
        latest = self.metrics[-1]
        last_hour = [m for m in self.metrics if m.timestamp > datetime.now() - timedelta(hours=1)]
        
        avg_cpu = sum(m.cpu_percent for m in last_hour) / len(last_hour) if last_hour else 0
        avg_memory = sum(m.memory_percent for m in last_hour) / len(last_hour) if last_hour else 0
        total_operations = sum(m.operations_per_minute for m in last_hour)
        
        return f"""
📊 **تقرير الأداء - آخر ساعة:**

💻 **المعالج:**
• الحالي: {latest.cpu_percent:.1f}%
• المتوسط: {avg_cpu:.1f}%

💾 **الذاكرة:**
• الحالي: {latest.memory_percent:.1f}%
• المتوسط: {avg_memory:.1f}%

⚡ **العمليات:**
• المجموع: {total_operations}
• متوسط وقت الاستجابة: {latest.response_time_avg:.2f}s

❌ **الأخطاء:** {self.error_count}
👥 **المستخدمين النشطين:** {latest.active_users}

🕐 **آخر تحديث:** {latest.timestamp.strftime('%H:%M:%S')}
        """
    
    def get_real_time_stats(self) -> Dict:
        """الحصول على إحصائيات فورية"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'active_operations': self.active_operations,
            'total_errors': self.error_count,
            'avg_response_time': sum(self.operation_times[-10:]) / 10 if self.operation_times else 0
        }

# إنشاء مثيل وحيد
performance_monitor = PerformanceMonitor()
