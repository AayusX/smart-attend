import { useState, useEffect } from 'react';
import { attendanceAPI } from '../services/api';
import { Filter, Search, Check, Clock, X } from 'lucide-react';

interface AttendanceRecord {
  id: number;
  student_id: number;
  student_name: string;
  student_code: string;
  session_date: string;
  status: string;
  check_in_time: string;
  confidence: number;
}

export default function Attendance() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [editingRecord, setEditingRecord] = useState<AttendanceRecord | null>(null);

  useEffect(() => { loadRecords(); }, [statusFilter]);

  const loadRecords = async () => {
    try {
      const response = await attendanceAPI.list({ status: statusFilter || undefined });
      setRecords(response.data);
    } catch (error) {
      console.error('Failed to load records:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCorrection = async (recordId: number, newStatus: string) => {
    try {
      await attendanceAPI.correct(recordId, { status: newStatus, reason: 'Manual correction' });
      setEditingRecord(null);
      loadRecords();
    } catch (error) {
      console.error('Failed to correct:', error);
    }
  };

  const filtered = records.filter((r) =>
    searchQuery ? r.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.student_code?.toLowerCase().includes(searchQuery.toLowerCase()) : true
  );

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in">
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Attendance Records</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>View and manage attendance history</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6 flex items-center gap-4 animate-fade-in" style={{ animationDelay: '50ms' }}>
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
          <input type="text" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-11" />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field w-40">
          <option value="">All Status</option>
          <option value="present">Present</option>
          <option value="late">Late</option>
          <option value="absent">Absent</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden animate-fade-in" style={{ animationDelay: '100ms' }}>
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-[#D2D2D7] border-t-[#0071E3] rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b" style={{ borderColor: 'var(--divider)' }}>
                <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Student</th>
                <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Date</th>
                <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Time</th>
                <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Status</th>
                <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Confidence</th>
                <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((record, i) => (
                <tr key={record.id} className="table-row animate-fade-in" style={{ animationDelay: `${i * 20}ms` }}>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-white" style={{ backgroundColor: '#0071E3' }}>
                        {record.student_name?.charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{record.student_name}</p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{record.student_code}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>{record.session_date}</td>
                  <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {record.check_in_time ? new Date(record.check_in_time).toLocaleTimeString() : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`badge-${record.status === 'present' ? 'success' : record.status === 'late' ? 'warning' : 'error'}`}>
                      {record.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {record.confidence ? `${(record.confidence * 100).toFixed(0)}%` : '-'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => setEditingRecord(record)} className="text-sm font-medium" style={{ color: 'var(--accent)' }}>
                      Correct
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Correction Modal */}
      {editingRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.3)', backdropFilter: 'blur(4px)' }}>
          <div className="card w-full max-w-sm p-6 animate-scale-in">
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Correct Attendance</h3>
            <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>
              {editingRecord.student_name} - {editingRecord.session_date}
            </p>
            <div className="flex gap-2">
              {['present', 'late', 'absent'].map((s) => (
                <button key={s} onClick={() => handleCorrection(editingRecord.id, s)}
                  className={`flex-1 py-2.5 rounded-xl text-sm font-medium text-white ${
                    s === 'present' ? 'bg-[#34C759] hover:bg-[#2DB84E]' :
                    s === 'late' ? 'bg-[#FF9F0A] hover:bg-[#E88E00]' :
                    'bg-[#FF3B30] hover:bg-[#E0342A]'
                  }`} style={{ transition: 'background-color 0.15s' }}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
            <button onClick={() => setEditingRecord(null)} className="btn-secondary w-full mt-3">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
