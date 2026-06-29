import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AppShell } from './components/layout/AppShell'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { StudentsPage } from './pages/StudentsPage'
import { GradesPage } from './pages/GradesPage'
import { AdmissionPage } from './pages/AdmissionPage'
import { FeeVouchersPage } from './pages/FeeVouchersPage'
import { FeeReportsPage } from './pages/FeeReportsPage'
import { ExtraChargesPage } from './pages/ExtraChargesPage'
import { AttendancePage } from './pages/AttendancePage'
import { SchoolSettingsPage } from './pages/SchoolSettingsPage'
import { UserManagementPage } from './pages/UserManagementPage'
import { BackupPage } from './pages/BackupPage'
import { StudentSearchPage } from './pages/StudentSearchPage'
import { StudentFeePage } from './pages/StudentFeePage'
import { PromoteStudentsPage } from './pages/PromoteStudentsPage'
import { FeeStatusPage } from './pages/FeeStatusPage'

const queryClient = new QueryClient()
const theme = createTheme({ palette: { mode: 'light', primary: { main: '#1565c0' } } })

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<AppShell />}>
                  {/* Dashboard is intentionally open to every authenticated role —
                      it renders different content per role internally (Teacher
                      sees a redirect message rather than being blocked here). */}
                  <Route path="/" element={<DashboardPage />} />

                  <Route element={<ProtectedRoute allowedRoles={['Admin', 'Accountant']} />}>
                    <Route path="/students" element={<StudentsPage />} />
                    <Route path="/students/search" element={<StudentSearchPage />} />
                    <Route path="/students/new" element={<AdmissionPage />} />
                    <Route path="/grades" element={<GradesPage />} />
                    <Route path="/fees/student" element={<StudentFeePage />} />
                    <Route path="/fees/student/:studentId" element={<StudentFeePage />} />
                    <Route path="/fees/vouchers" element={<FeeVouchersPage />} />
                    <Route path="/fees/reports" element={<FeeReportsPage />} />
                    <Route path="/charges" element={<ExtraChargesPage />} />
                  </Route>

                  <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
                    <Route path="/students/promote" element={<PromoteStudentsPage />} />
                    <Route path="/settings" element={<SchoolSettingsPage />} />
                    <Route path="/users" element={<UserManagementPage />} />
                    <Route path="/backup" element={<BackupPage />} />
                  </Route>

                  <Route element={<ProtectedRoute allowedRoles={['Admin', 'Teacher']} />}>
                    <Route path="/attendance" element={<AttendancePage />} />
                  </Route>

                  <Route element={<ProtectedRoute allowedRoles={['Teacher']} />}>
                    <Route path="/fees/status" element={<FeeStatusPage />} />
                  </Route>
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  )
}
