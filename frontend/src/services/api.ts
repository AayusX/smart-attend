import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password })),
  register: (username: string, password: string, role: string = 'teacher') =>
    api.post('/auth/register', { username, password, role }),
  getMe: () => api.get('/auth/me'),
};

// Students API
export const studentsAPI = {
  list: (params?: any) => api.get('/students', { params }),
  get: (id: number) => api.get(`/students/${id}`),
  create: (data: any) => api.post('/students', data),
  update: (id: number, data: any) => api.put(`/students/${id}`, data),
  delete: (id: number) => api.delete(`/students/${id}`),
  getClasses: () => api.get('/students/classes/list'),
};

// Attendance API
export const attendanceAPI = {
  list: (params?: any) => api.get('/attendance', { params }),
  getToday: () => api.get('/attendance/today'),
  getStats: (date?: string) => api.get('/attendance/stats', { params: { target_date: date } }),
  correct: (recordId: number, data: any) => api.put(`/attendance/${recordId}/correct`, data),
  getStudentHistory: (studentId: number, days?: number) =>
    api.get(`/attendance/student/${studentId}`, { params: { days } }),
  getEvents: (limit?: number) => api.get('/attendance/events', { params: { limit } }),
};

// Enrollment API
export const enrollmentAPI = {
  start: (studentId: number, numSamples: number = 5) =>
    api.post('/enrollment/start', { student_id: studentId, num_samples: numSamples }),
  getStatus: () => api.get('/enrollment/status'),
  stop: () => api.post('/enrollment/stop'),
  deleteTemplate: (studentId: number) => api.delete(`/enrollment/student/${studentId}`),
  listTemplates: () => api.get('/enrollment/templates'),
};

// Reports API
export const reportsAPI = {
  getDaily: (date?: string, className?: string) =>
    api.get('/reports/daily', { params: { target_date: date, class_name: className } }),
  getMonthly: (year?: number, month?: number, className?: string) =>
    api.get('/reports/monthly', { params: { year, month, class_name: className } }),
  getStudentReport: (studentId: number, startDate?: string, endDate?: string) =>
    api.get(`/reports/student/${studentId}`, { params: { start_date: startDate, end_date: endDate } }),
  exportCSV: (startDate: string, endDate: string, className?: string) =>
    api.get('/reports/export/csv', {
      params: { start_date: startDate, end_date: endDate, class_name: className },
      responseType: 'blob',
    }),
};

// Camera API
export const cameraAPI = {
  start: () => api.post('/camera/start'),
  stop: () => api.post('/camera/stop'),
  getStatus: () => api.get('/camera/status'),
  reloadEmbeddings: () => api.post('/recognition/load-embeddings'),
};

export default api;
