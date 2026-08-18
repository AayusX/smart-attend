import { useState, useEffect } from 'react';
import { reportsAPI } from '../services/api';
import { Download, Calendar, Users, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DailyReport {
  date: string;
  summary: { total: number; present: number; late: number; absent: number; attendance_percentage: number; };
  students: Array<{ student_id: number; student_code: string; student_name: string; status: string; check_in_time: string; }>;
}

export default function Reports() {
  const [activeTab, setActiveTab] = useState<'daily' | 'monthly'>('daily');
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => { loadReport(); }, [activeTab, selectedDate, selectedMonth, selectedYear]);

  const loadReport = async () => {
    setIsLoading(true);
    try {
      if (activeTab === 'daily') {
        const res = await reportsAPI.getDaily(selectedDate);
        setDailyReport(res.data);
      }
    } catch {} finally { setIsLoading(false); }
  };

  const chartData = dailyReport?.students.map((s) => ({
    name: s.student_name.split(' ')[0],
    present: s.status === 'present' ? 1 : 0,
    late: s.status === 'late' ? 1 : 0,
    absent: s.status === 'absent' ? 1 : 0,
  })) || [];

  const exportCSV = async () => {
    try {
      const end = new Date().toISOString().split('T')[0];
      const start = new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0];
      const res = await reportsAPI.exportCSV(start, end);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = `attendance_${start}_${end}.csv`;
      document.body.appendChild(a); a.click(); a.remove();
    } catch {}
  };

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Reports</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Attendance analytics and exports</p>
        </div>
        <button onClick={exportCSV} className="btn-primary flex items-center gap-2">
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 animate-fade-in" style={{ animationDelay: '50ms' }}>
        {[{ key: 'daily', label: 'Daily', icon: Calendar }, { key: 'monthly', label: 'Monthly', icon: Users }].map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.key ? 'text-white' : ''
            }`} style={{
              backgroundColor: activeTab === tab.key ? 'var(--accent)' : 'var(--bg-surface)',
              color: activeTab === tab.key ? 'white' : 'var(--text-secondary)',
              boxShadow: activeTab === tab.key ? '0 2px 8px rgba(0,113,227,0.2)' : 'var(--shadow-sm)',
            }}>
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6 animate-fade-in" style={{ animationDelay: '100ms' }}>
        {activeTab === 'daily' ? (
          <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="input-field w-60" />
        ) : (
          <div className="flex gap-3">
            <select value={selectedMonth} onChange={(e) => setSelectedMonth(Number(e.target.value))} className="input-field w-40">
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>{new Date(2024, i).toLocaleString('default', { month: 'long' })}</option>
              ))}
            </select>
            <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))} className="input-field w-28">
              <option value={2025}>2025</option>
              <option value={2026}>2026</option>
            </select>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-[#D2D2D7] border-t-[#0071E3] rounded-full animate-spin" />
        </div>
      ) : activeTab === 'daily' && dailyReport ? (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-5 gap-4 animate-fade-in" style={{ animationDelay: '150ms' }}>
            {[
              { label: 'Total', value: dailyReport.summary.total, color: 'var(--text-primary)' },
              { label: 'Present', value: dailyReport.summary.present, color: 'var(--success)' },
              { label: 'Late', value: dailyReport.summary.late, color: 'var(--warning)' },
              { label: 'Absent', value: dailyReport.summary.absent, color: 'var(--error)' },
              { label: 'Attendance', value: `${dailyReport.summary.attendance_percentage}%`, color: 'var(--accent)' },
            ].map((s, i) => (
              <div key={i} className="stat-card">
                <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>{s.label}</p>
                <p className="text-2xl font-semibold" style={{ color: s.color }}>{s.value}</p>
              </div>
            ))}
          </div>

          {/* Chart */}
          <div className="card p-6 animate-fade-in" style={{ animationDelay: '200ms' }}>
            <h3 className="text-base font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Attendance Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData.slice(0, 20)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6E6E73' }} />
                <YAxis tick={{ fontSize: 11, fill: '#6E6E73' }} />
                <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E8E8ED', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }} />
                <Bar dataKey="present" fill="#34C759" radius={[4, 4, 0, 0]} />
                <Bar dataKey="late" fill="#FF9F0A" radius={[4, 4, 0, 0]} />
                <Bar dataKey="absent" fill="#FF3B30" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Table */}
          <div className="card overflow-hidden animate-fade-in" style={{ animationDelay: '250ms' }}>
            <table className="w-full">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--divider)' }}>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Student</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Code</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Status</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Time</th>
                </tr>
              </thead>
              <tbody>
                {dailyReport.students.map((s, i) => (
                  <tr key={s.student_id} className="table-row">
                    <td className="px-6 py-3.5 text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{s.student_name}</td>
                    <td className="px-6 py-3.5 text-sm font-mono" style={{ color: 'var(--accent)' }}>{s.student_code}</td>
                    <td className="px-6 py-3.5">
                      <span className={`badge-${s.status === 'present' ? 'success' : s.status === 'late' ? 'warning' : 'error'}`}>{s.status}</span>
                    </td>
                    <td className="px-6 py-3.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      {s.check_in_time ? new Date(s.check_in_time).toLocaleTimeString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
