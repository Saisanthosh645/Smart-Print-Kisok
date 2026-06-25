import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api

export const auth = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  verifyEmail: (token) => api.post(`/auth/verify-email?token=${token}`),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (data) => api.post('/auth/reset-password', data),
}

export const student = {
  uploadDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/student/documents/upload', form)
  },
  listDocuments: () => api.get('/student/documents'),
  estimate: (data) => api.post('/student/estimate', data),
  createJob: (data) => api.post('/student/jobs', data),
  listJobs: () => api.get('/student/jobs'),
  getJob: (id) => api.get(`/student/jobs/${id}`),
  createPayment: (id) => api.post(`/student/jobs/${id}/pay`),
  verifyPayment: (id, data) => api.post(`/student/jobs/${id}/verify-payment`, data),
  recommendations: (documentId) => api.get('/student/recommendations', { params: { document_id: documentId } }),
  notifications: () => api.get('/student/notifications'),
}

export const printCenter = {
  jobs: () => api.get('/print-center/jobs'),
  queue: () => api.get('/print-center/queue'),
  assign: (id) => api.post(`/print-center/jobs/${id}/assign`),
  start: (id) => api.post(`/print-center/jobs/${id}/start`),
  complete: (id) => api.post(`/print-center/jobs/${id}/complete`),
  fail: (id) => api.post(`/print-center/jobs/${id}/fail`),
  processQueue: () => api.post('/print-center/process-queue'),
  printers: () => api.get('/print-center/printers'),
}

export const admin = {
  analytics: () => api.get('/admin/analytics'),
  users: () => api.get('/admin/users'),
  banUser: (id, reason) => api.post(`/admin/users/${id}/ban`, { reason }),
  unbanUser: (id) => api.post(`/admin/users/${id}/unban`),
  togglePremium: (id) => api.post(`/admin/users/${id}/premium`),
  refund: (id, reason) => api.post(`/admin/payments/${id}/refund`, { reason }),
  printers: () => api.get('/admin/printers'),
  addPrinter: (data) => api.post('/admin/printers', data),
  updateHealth: (id, score) => api.patch(`/admin/printers/${id}/health?health_score=${score}`),
  deactivatePrinter: (id) => api.delete(`/admin/printers/${id}`),
}
