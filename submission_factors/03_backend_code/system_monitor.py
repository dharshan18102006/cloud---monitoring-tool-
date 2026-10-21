import psutil
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.warning_thresholds = {
            'cpu': 80,
            'memory': 85,
            'disk': 90
        }

    def get_stats(self):
        cpu_total = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                p_info = proc.info
                if p_info['cpu_percent'] is None:
                    p_info['cpu_percent'] = 0.0
                if p_info['memory_percent'] is None:
                    p_info['memory_percent'] = 0.0
                processes.append(p_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        processes.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)

        return {
            'cpu': {
                'total': round(cpu_total, 1),
                'per_core': cpu_per_core,
                'cores': len(cpu_per_core)
            },
            'memory': {
                'total': memory.total,
                'used': memory.used,
                'free': memory.free,
                'percent': round(memory.percent, 1)
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': round(disk.percent, 1)
            },
            'processes': processes[:20]
        }

    def get_warnings(self, stats):
        warnings = []
        ts = datetime.now().isoformat()

        if stats['cpu']['total'] > self.warning_thresholds['cpu']:
            warnings.append({'type': 'CPU', 'level': 'WARNING',
                'message': f"CPU usage at {stats['cpu']['total']}%", 'timestamp': ts})
        if stats['memory']['percent'] > self.warning_thresholds['memory']:
            warnings.append({'type': 'Memory', 'level': 'WARNING',
                'message': f"Memory usage at {stats['memory']['percent']}%", 'timestamp': ts})
        if stats['disk']['percent'] > self.warning_thresholds['disk']:
            warnings.append({'type': 'Disk', 'level': 'WARNING',
                'message': f"Disk usage at {stats['disk']['percent']}%", 'timestamp': ts})

        for proc in stats['processes'][:5]:
            if (proc.get('cpu_percent') or 0) > 50:
                warnings.append({'type': 'Process', 'level': 'HIGH_CPU',
                    'message': f"Process '{proc['name']}' (PID {proc['pid']}) using {proc['cpu_percent']:.1f}% CPU",
                    'timestamp': ts})
        return warnings
