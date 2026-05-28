import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import UploadCenterPage from '@/pages/UploadCenterPage'
import ReviewQueuePage from '@/pages/ReviewQueuePage'
import FlaggedRecordsPage from '@/pages/FlaggedRecordsPage'
import AuditHistoryPage from '@/pages/AuditHistoryPage'
import SourceManagementPage from '@/pages/SourceManagementPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="upload" element={<UploadCenterPage />} />
        <Route path="review" element={<ReviewQueuePage />} />
        <Route path="flagged" element={<FlaggedRecordsPage />} />
        <Route path="audit" element={<AuditHistoryPage />} />
        <Route path="sources" element={<SourceManagementPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
