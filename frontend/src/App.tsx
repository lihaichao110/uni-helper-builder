import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Spin } from 'antd'
import { bootstrapSession } from './api'
import { useAuthStore } from './store/auth'
import AppLayout from './components/AppLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ProjectsPage from './pages/ProjectsPage'
import CredentialsPage from './pages/CredentialsPage'
import BuildsPage from './pages/BuildsPage'
import BuildDetailPage from './pages/BuildDetailPage'
import UsersPage from './pages/UsersPage'
import AuditPage from './pages/AuditPage'

export default function App() {
  const { user, bootstrapped, setUser, setBootstrapped } = useAuthStore()
  useEffect(() => {
    bootstrapSession()
      .then(setUser)
      .finally(() => setBootstrapped(true))
  }, [setUser, setBootstrapped])
  if (!bootstrapped)
    return (
      <div className="center-screen">
        <Spin size="large" />
      </div>
    )
  if (!user)
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route
          path="/credentials"
          element={user.role === 'admin' ? <CredentialsPage /> : <Navigate to="/" />}
        />
        <Route path="/builds" element={<BuildsPage />} />
        <Route path="/builds/:id" element={<BuildDetailPage />} />
        <Route
          path="/users"
          element={user.role === 'admin' ? <UsersPage /> : <Navigate to="/" />}
        />
        <Route
          path="/audit"
          element={user.role === 'admin' ? <AuditPage /> : <Navigate to="/" />}
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
