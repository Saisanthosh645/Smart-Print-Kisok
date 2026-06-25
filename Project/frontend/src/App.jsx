import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import VerifyEmail from './pages/VerifyEmail'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import StudentDashboard from './pages/student/Dashboard'
import Upload from './pages/student/Upload'
import Jobs from './pages/student/Jobs'
import JobDetail from './pages/student/JobDetail'
import PrintCenter from './pages/print-center/Dashboard'
import QueueView from './pages/print-center/QueueView'
import AdminDashboard from './pages/admin/Dashboard'
import UserManagement from './pages/admin/UserManagement'
import PrinterManagement from './pages/admin/PrinterManagement'

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />
  return children
}

function RoleRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'admin') return <Navigate to="/admin" replace />
  if (user.role === 'print_center') return <Navigate to="/print-center" replace />
  return <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/home" element={<RoleRedirect />} />

        <Route path="/dashboard" element={
          <ProtectedRoute roles={['student']}><StudentDashboard /></ProtectedRoute>
        } />
        <Route path="/upload" element={
          <ProtectedRoute roles={['student']}><Upload /></ProtectedRoute>
        } />
        <Route path="/jobs" element={
          <ProtectedRoute roles={['student']}><Jobs /></ProtectedRoute>
        } />
        <Route path="/jobs/:id" element={
          <ProtectedRoute roles={['student']}><JobDetail /></ProtectedRoute>
        } />

        <Route path="/print-center" element={
          <ProtectedRoute roles={['print_center', 'admin']}><PrintCenter /></ProtectedRoute>
        } />
        <Route path="/print-center/queue" element={
          <ProtectedRoute roles={['print_center', 'admin']}><QueueView /></ProtectedRoute>
        } />

        <Route path="/admin" element={
          <ProtectedRoute roles={['admin']}><AdminDashboard /></ProtectedRoute>
        } />
        <Route path="/admin/users" element={
          <ProtectedRoute roles={['admin']}><UserManagement /></ProtectedRoute>
        } />
        <Route path="/admin/printers" element={
          <ProtectedRoute roles={['admin']}><PrinterManagement /></ProtectedRoute>
        } />
      </Route>
    </Routes>
  )
}
