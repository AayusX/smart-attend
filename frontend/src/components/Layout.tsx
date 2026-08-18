import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard,
  Users,
  UserCheck,
  Camera,
  FileBarChart,
  LogOut,
  Wifi,
  WifiOff,
  Clock,
  Settings,
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useState, useEffect } from 'react';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Students', href: '/students', icon: Users },
  { name: 'Attendance', href: '/attendance', icon: UserCheck },
  { name: 'Enrollment', href: '/enrollment', icon: Camera },
  { name: 'Reports', href: '/reports', icon: FileBarChart },
];

function NepaliClock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const kt = time.toLocaleString('en-US', {
    timeZone: 'Asia/Kathmandu',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });

  return (
    <span className="flex items-center gap-1.5 text-xs text-[#6E6E73] font-medium">
      <Clock className="w-3.5 h-3.5" />
      {kt}
    </span>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { isConnected } = useWebSocket('live-attendance');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col border-r"
        style={{
          width: sidebarCollapsed ? '72px' : '240px',
          backgroundColor: 'var(--bg-surface)',
          borderColor: 'var(--divider)',
          transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b" style={{ borderColor: 'var(--divider)' }}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
            <Camera className="w-5 h-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div>
              <h1 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>SmartAttend</h1>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Face Recognition</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`nav-item ${isActive ? 'active' : ''}`}
                title={sidebarCollapsed ? item.name : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* System Status */}
        {!sidebarCollapsed && (
          <div className="px-4 py-3 mx-3 mb-3 rounded-xl" style={{ backgroundColor: 'var(--bg-primary)' }}>
            <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
              {isConnected ? (
                <>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--success)' }} />
                  <span>System Online</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--error)' }} />
                  <span>Disconnected</span>
                </>
              )}
            </div>
          </div>
        )}

        {/* User */}
        <div className="border-t px-4 py-4" style={{ borderColor: 'var(--divider)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold text-white" style={{ backgroundColor: 'var(--accent)' }}>
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            {!sidebarCollapsed && (
              <>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>{user?.username}</p>
                  <p className="text-xs capitalize" style={{ color: 'var(--text-secondary)' }}>{user?.role}</p>
                </div>
                <button onClick={handleLogout} className="p-2 rounded-lg transition-colors" style={{ color: 'var(--text-secondary)' }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}>
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
