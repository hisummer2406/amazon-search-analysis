# monitoring.py
import asyncio
import json
from datetime import datetime
from typing import Dict, List
import psutil


class SystemMonitor:
    """系统性能监控"""

    def __init__(self):
        self.metrics_history = []
        self.alerts = []

    async def collect_metrics(self) -> Dict:
        """收集系统指标"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'total': cpu_percent,
                'cores': cpu_per_core,
                'load_avg': psutil.getloadavg()[:3] if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            },
            'memory': {
                'percent': memory.percent,
                'available_gb': memory.available / (1024 ** 3),
                'used_gb': memory.used / (1024 ** 3)
            },
            'disk': {
                'percent': disk.percent,
                'free_gb': disk.free / (1024 ** 3)
            },
            'processes': len(psutil.pids())
        }

        self.metrics_history.append(metrics)

        # 检查告警条件
        await self.check_alerts(metrics)

        return metrics

    async def check_alerts(self, metrics: Dict):
        """检查告警条件"""
        alerts = []

        # CPU告警
        if metrics['cpu']['total'] > 90:
            alerts.append({
                'level': 'warning',
                'message': f"CPU使用率过高: {metrics['cpu']['total']:.1f}%"
            })

        # 内存告警
        if metrics['memory']['percent'] > 85:
            alerts.append({
                'level': 'warning',
                'message': f"内存使用率过高: {metrics['memory']['percent']:.1f}%"
            })

        # 磁盘空间告警
        if metrics['disk']['percent'] > 80:
            alerts.append({
                'level': 'critical',
                'message': f"磁盘空间不足: {metrics['disk']['percent']:.1f}%"
            })

        # 记录告警
        for alert in alerts:
            alert['timestamp'] = datetime.now().isoformat()
            self.alerts.append(alert)
            print(f"🚨 [{alert['level'].upper()}] {alert['message']}")

    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}

        recent_metrics = self.metrics_history[-10:]  # 最近10次记录

        avg_cpu = sum(m['cpu']['total'] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m['memory']['percent'] for m in recent_metrics) / len(recent_metrics)

        return {
            'avg_cpu_usage': round(avg_cpu, 1),
            'avg_memory_usage': round(avg_memory, 1),
            'cpu_core_utilization': [
                round(sum(m['cpu']['cores'][i] for m in recent_metrics) / len(recent_metrics), 1)
                for i in range(4)  # 4核CPU
            ],
            'recent_alerts_count': len([a for a in self.alerts if
                                        datetime.fromisoformat(a['timestamp']) >
                                        datetime.now().replace(hour=datetime.now().hour - 1)
                                        ])
        }
