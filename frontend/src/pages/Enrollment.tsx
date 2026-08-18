import { useState, useEffect } from 'react';
import { studentsAPI, enrollmentAPI } from '../services/api';
import { Camera, Check, X, Trash2, RefreshCw, UserPlus, Shield } from 'lucide-react';

interface Student { id: number; student_code: string; full_name: string; has_face_template: boolean; }
interface Template { id: number; student_id: number; student_name: string; student_code: string; quality_score: number; created_at: string; }

export default function Enrollment() {
  const [students, setStudents] = useState<Student[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [enrollmentActive, setEnrollmentActive] = useState(false);
  const [samplesCaptured, setSamplesCaptured] = useState(0);
  const [samplesRequired, setSamplesRequired] = useState(5);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [numSamples, setNumSamples] = useState(5);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [s, t] = await Promise.all([studentsAPI.list(), enrollmentAPI.listTemplates()]);
      setStudents(s.data);
      setTemplates(t.data);
    } catch {} finally { setIsLoading(false); }
  };

  const startEnrollment = async () => {
    if (!selectedStudent) return;
    try {
      setMessage({ type: '', text: '' });
      await enrollmentAPI.start(selectedStudent, numSamples);
      setEnrollmentActive(true);
      setSamplesCaptured(0);
      setSamplesRequired(numSamples);
      setMessage({ type: 'success', text: 'Enrollment started. Position your face in the camera.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to start' });
    }
  };

  const stopEnrollment = async () => {
    try { await enrollmentAPI.stop(); setEnrollmentActive(false); setMessage({ type: 'success', text: 'Enrollment cancelled' }); } catch {}
  };

  const deleteTemplate = async (studentId: number) => {
    if (confirm('Delete this face template?')) {
      try { await enrollmentAPI.deleteTemplate(studentId); loadData(); } catch {}
    }
  };

  const unenrolled = students.filter((s) => !s.has_face_template);

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in">
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Face Enrollment</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Enroll students for face recognition</p>
      </div>

      {message.text && (
        <div className={`card p-4 mb-6 flex items-center gap-2.5 animate-scale-in ${
          message.type === 'success' ? 'border-l-4 border-l-[#34C759]' : 'border-l-4 border-l-[#FF3B30]'
        }`}>
          <p className="text-sm" style={{ color: message.type === 'success' ? 'var(--success)' : 'var(--error)' }}>{message.text}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Enrollment Panel */}
        <div className="card p-6 animate-fade-in" style={{ animationDelay: '50ms' }}>
          <h2 className="text-lg font-semibold mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Camera className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            Start Enrollment
          </h2>

          {enrollmentActive ? (
            <div className="space-y-5">
              <div className="p-5 rounded-xl" style={{ backgroundColor: '#0071E310', border: '1px solid #0071E330' }}>
                <p className="text-sm font-medium" style={{ color: 'var(--accent)' }}>Enrollment Active</p>
                <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                  Samples: {samplesCaptured} / {samplesRequired}
                </p>
                <div className="mt-3 h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--divider)' }}>
                  <div className="h-full rounded-full transition-all duration-500" style={{ backgroundColor: 'var(--accent)', width: `${(samplesCaptured / samplesRequired) * 100}%` }} />
                </div>
              </div>
              <button onClick={stopEnrollment} className="btn-secondary w-full flex items-center justify-center gap-2"
                style={{ borderColor: '#FF3B3040', color: 'var(--error)' }}>
                <X className="w-4 h-4" /> Cancel Enrollment
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Select Student</label>
                <select value={selectedStudent || ''} onChange={(e) => setSelectedStudent(Number(e.target.value))} className="input-field">
                  <option value="">Choose a student...</option>
                  {unenrolled.map((s) => (
                    <option key={s.id} value={s.id}>{s.student_code} - {s.full_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Samples Required</label>
                <input type="number" min="3" max="15" value={numSamples} onChange={(e) => setNumSamples(Number(e.target.value))}
                  className="input-field" />
              </div>
              <button onClick={startEnrollment} disabled={!selectedStudent}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-40">
                <Camera className="w-4 h-4" /> Start Enrollment
              </button>
              <p className="text-center text-xs" style={{ color: 'var(--text-secondary)' }}>
                {unenrolled.length} student{unenrolled.length !== 1 ? 's' : ''} pending enrollment
              </p>
            </div>
          )}
        </div>

        {/* Enrolled List */}
        <div className="card p-6 animate-fade-in" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <Shield className="w-5 h-5" style={{ color: 'var(--success)' }} />
              Enrolled ({templates.length})
            </h2>
            <button onClick={loadData} className="p-2 rounded-lg transition-colors" style={{ color: 'var(--text-secondary)' }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-primary)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}>
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {templates.length === 0 ? (
              <div className="flex flex-col items-center py-12">
                <UserPlus className="w-10 h-10 mb-3" style={{ color: 'var(--divider)' }} />
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>No students enrolled yet</p>
              </div>
            ) : (
              templates.map((t, i) => (
                <div key={t.id} className="flex items-center justify-between p-3 rounded-xl animate-fade-in"
                  style={{ backgroundColor: 'var(--bg-primary)', animationDelay: `${i * 20}ms` }}>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: '#34C75920' }}>
                      <Check className="w-4 h-4" style={{ color: 'var(--success)' }} />
                    </div>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{t.student_name}</p>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{t.student_code}</p>
                    </div>
                  </div>
                  <button onClick={() => deleteTemplate(t.student_id)} className="p-2 rounded-lg transition-colors"
                    style={{ color: 'var(--text-secondary)' }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#FF3B3010'; e.currentTarget.style.color = 'var(--error)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}>
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
