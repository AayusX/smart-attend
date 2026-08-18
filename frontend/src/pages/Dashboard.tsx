import { useState, useEffect } from 'react';
import { attendanceAPI, cameraAPI } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  Users, UserCheck, UserX, Clock, TrendingUp,
  Play, Square, Activity, Wifi, WifiOff,
  Camera, Shield, Zap, ArrowUpRight
} from 'lucide-react';

interface AttendanceStats {
  total_students: number;
  present: number;
  late: number;
  absent: number;
  attendance_percentage: number;
}

interface LiveEvent {
  event: string;
  student_name: string;
  student_code: string;
  status: string;
  confidence: number;
  timestamp: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<AttendanceStats | null>(null);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [cameraRunning, setCameraRunning] = useState(false);
  const [cameraFps, setCameraFps] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const { isConnected, lastMessage } = useWebSocket('live-attendance');

  useEffect(() => { loadStats(); }, []);

  useEffect(() => {
    if (lastMessage?.event === 'attendance_marked') {
      setLiveEvents((prev) => [lastMessage as LiveEvent, ...prev].slice(0, 15));
      loadStats();
    }
  }, [lastMessage]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await cameraAPI.getStatus();
        setCameraFps(res.data?.recognition?.fps || 0);
        setCameraRunning(res.data?.camera?.is_running || false);
      } catch {}
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await attendanceAPI.getToday();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCamera = async () => {
    try {
      if (cameraRunning) {
        await cameraAPI.stop();
        setCameraRunning(false);
      } else {
        await cameraAPI.start();
        setCameraRunning(true);
      }
    } catch (error) {
      console.error('Failed to toggle camera:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-8 h-8 border-2 border-[#D2D2D7] border-t-[#0071E3] rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Overview</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
            Today's attendance at a glance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl" style={{ backgroundColor: 'var(--bg-surface)', boxShadow: 'var(--shadow-sm)' }}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#34C759]' : 'bg-[#FF3B30]'}`} />
            <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              {isConnected ? 'Connected' : 'Offline'}
            </span>
          </div>
          <button
            onClick={toggleCamera}
            className="btn-primary flex items-center gap-2"
          >
            {cameraRunning ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {cameraRunning ? 'Stop Camera' : 'Start Camera'}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <StatCard title="Total Students" value={stats?.total_students || 0} icon={Users} color="#6E6E73" delay={0} />
        <StatCard title="Present" value={stats?.present || 0} icon={UserCheck} color="#34C759" delay={50} />
        <StatCard title="Late" value={stats?.late || 0} icon={Clock} color="#FF9F0A" delay={100} />
        <StatCard title="Absent" value={stats?.absent || 0} icon={UserX} color="#FF3B30" delay={150} />
        <StatCard title="Attendance" value={`${stats?.attendance_percentage || 0}%`} icon={TrendingUp} color="#0071E3" delay={200} />
      </div>

      {/* Live Feed + Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Attendance */}
        <div className="lg:col-span-2 card p-6 animate-fade-in" style={{ animationDelay: '250ms' }}>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Recent Attendance</h2>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#34C759] animate-pulse' : 'bg-[#FF3B30]'}`} />
              <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Live</span>
            </div>
          </div>
          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
            {liveEvents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Camera className="w-10 h-10 mb-3" style={{ color: 'var(--divider)' }} />
                <p style={{ color: 'var(--text-secondary)' }}>No recent activity</p>
                <p className="text-xs mt-1" style={{ color: 'var(--divider)' }}>Start the camera to begin</p>
              </div>
            ) : (
              liveEvents.map((event, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3.5 rounded-xl animate-slide-in"
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    animationDelay: `${index * 30}ms`,
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold text-white" style={{ backgroundColor: '#0071E3' }}>
                      {event.student_name?.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{event.student_name}</p>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{event.student_code}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${
                      event.status === 'present' ? 'badge-success' :
                      event.status === 'late' ? 'badge-warning' : 'badge-error'
                    }`}>
                      {event.status}
                    </span>
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                      {event.confidence ? `${(event.confidence * 100).toFixed(0)}%` : ''}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* System Panel */}
        <div className="card p-6 animate-fade-in" style={{ animationDelay: '300ms' }}>
          <h2 className="text-lg font-semibold mb-5" style={{ color: 'var(--text-primary)' }}>System Status</h2>
          <div className="space-y-4">
            <StatusRow label="Camera" value={cameraRunning ? 'Online' : 'Offline'} ok={cameraRunning} icon={Camera} />
            <StatusRow label="AI Engine" value="Ready" ok={true} icon={Zap} />
            <StatusRow label="FPS" value={`${cameraFps.toFixed(0)} fps`} ok={cameraFps > 15} icon={Activity} />
            <StatusRow label="WebSocket" value={isConnected ? 'Connected' : 'Disconnected'} ok={isConnected} icon={isConnected ? Wifi : WifiOff} />
            <StatusRow label="Database" value="Healthy" ok={true} icon={Shield} />
          </div>

          <div className="mt-6 pt-5 border-t" style={{ borderColor: 'var(--divider)' }}>
            <p className="text-xs font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>Performance</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-primary)' }}>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Students</p>
                <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{stats?.total_students || 0}</p>
              </div>
              <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-primary)' }}>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Present %</p>
                <p className="text-lg font-semibold" style={{ color: 'var(--accent)' }}>{stats?.attendance_percentage || 0}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color, delay }: any) {
  return (
    <div className="stat-card animate-fade-in" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        <ArrowUpRight className="w-4 h-4" style={{ color: 'var(--divider)' }} />
      </div>
      <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>{title}</p>
      <p className="text-2xl font-semibold animate-count" style={{ color: 'var(--text-primary)' }}>{value}</p>
    </div>
  );
}

function StatusRow({ label, value, ok, icon: Icon }: any) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <Icon className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: ok ? 'var(--success)' : 'var(--error)' }} />
        <span className="text-xs font-medium" style={{ color: ok ? 'var(--success)' : 'var(--error)' }}>{value}</span>
      </div>
    </div>
  );
}
