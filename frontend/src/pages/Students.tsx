import { useState, useEffect } from 'react';
import { studentsAPI } from '../services/api';
import { Plus, Search, Edit, Trash2, X, ChevronDown, Filter, MoreHorizontal, UserPlus, Check } from 'lucide-react';

interface Student {
  id: number;
  student_code: string;
  full_name: string;
  class_name: string;
  section: string;
  roll_number: string;
  status: string;
  has_face_template: boolean;
}

export default function Students() {
  const [students, setStudents] = useState<Student[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [formData, setFormData] = useState({
    student_code: '', full_name: '', class_name: '', section: '', roll_number: '',
  });

  useEffect(() => { loadStudents(); }, []);

  const loadStudents = async () => {
    try {
      const response = await studentsAPI.list({ search: searchQuery || undefined });
      setStudents(response.data);
    } catch (error) {
      console.error('Failed to load students:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingStudent) {
        await studentsAPI.update(editingStudent.id, formData);
      } else {
        await studentsAPI.create(formData);
      }
      setShowModal(false);
      setEditingStudent(null);
      resetForm();
      loadStudents();
    } catch (error) {
      console.error('Failed to save student:', error);
    }
  };

  const handleEdit = (student: Student) => {
    setEditingStudent(student);
    setFormData({
      student_code: student.student_code, full_name: student.full_name,
      class_name: student.class_name || '', section: student.section || '',
      roll_number: student.roll_number || '',
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Deactivate this student?')) {
      try { await studentsAPI.delete(id); loadStudents(); } catch {}
    }
  };

  const resetForm = () => {
    setFormData({ student_code: '', full_name: '', class_name: '', section: '', roll_number: '' });
  };

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Students</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
            {students.length} student{students.length !== 1 ? 's' : ''} enrolled
          </p>
        </div>
        <button onClick={() => { resetForm(); setEditingStudent(null); setShowModal(true); }} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Student
        </button>
      </div>

      {/* Search */}
      <div className="card p-4 mb-6 animate-fade-in" style={{ animationDelay: '50ms' }}>
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="Search by name, code, or class..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); }}
            className="input-field pl-11"
          />
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden animate-fade-in" style={{ animationDelay: '100ms' }}>
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-[#D2D2D7] border-t-[#0071E3] rounded-full animate-spin" />
          </div>
        ) : students.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <UserPlus className="w-12 h-12 mb-4" style={{ color: 'var(--divider)' }} />
            <p className="text-base font-medium" style={{ color: 'var(--text-primary)' }}>No students yet</p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Add your first student to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--divider)' }}>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Code</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Name</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Class</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Roll</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Face</th>
                  <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student, i) => (
                  <tr key={student.id} className="table-row animate-fade-in" style={{ animationDelay: `${i * 20}ms` }}>
                    <td className="px-6 py-4">
                      <span className="text-sm font-mono font-medium" style={{ color: 'var(--accent)' }}>{student.student_code}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-white" style={{ backgroundColor: '#0071E3' }}>
                          {student.full_name?.charAt(0)}
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{student.full_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>{student.class_name || '-'}</td>
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>{student.roll_number || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={student.has_face_template ? 'badge-success' : 'badge-neutral'}>
                        {student.has_face_template ? 'Enrolled' : 'Not Enrolled'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => handleEdit(student)} className="p-2 rounded-lg transition-colors" style={{ color: 'var(--text-secondary)' }}
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-primary)'; }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}>
                          <Edit className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(student.id)} className="p-2 rounded-lg transition-colors" style={{ color: 'var(--error)' }}
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#FF3B3010'; }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}>
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.3)', backdropFilter: 'blur(4px)' }}>
          <div className="card w-full max-w-md p-0 animate-scale-in">
            <div className="flex items-center justify-between px-6 py-5 border-b" style={{ borderColor: 'var(--divider)' }}>
              <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                {editingStudent ? 'Edit Student' : 'Add Student'}
              </h2>
              <button onClick={() => { setShowModal(false); setEditingStudent(null); }} className="p-2 rounded-lg transition-colors"
                style={{ color: 'var(--text-secondary)' }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-primary)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Student Code</label>
                <input type="text" value={formData.student_code} onChange={(e) => setFormData({ ...formData, student_code: e.target.value })}
                  className="input-field" placeholder="e.g. STU-001" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Full Name</label>
                <input type="text" value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="input-field" placeholder="e.g. Aayush Bhandari" required />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Class</label>
                  <input type="text" value={formData.class_name} onChange={(e) => setFormData({ ...formData, class_name: e.target.value })}
                    className="input-field" placeholder="e.g. 10" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Section</label>
                  <input type="text" value={formData.section} onChange={(e) => setFormData({ ...formData, section: e.target.value })}
                    className="input-field" placeholder="e.g. A" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-primary)' }}>Roll No</label>
                  <input type="text" value={formData.roll_number} onChange={(e) => setFormData({ ...formData, roll_number: e.target.value })}
                    className="input-field" placeholder="e.g. 01" />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setShowModal(false); setEditingStudent(null); }} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" className="btn-primary flex-1 flex items-center justify-center gap-2">
                  <Check className="w-4 h-4" />
                  {editingStudent ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
