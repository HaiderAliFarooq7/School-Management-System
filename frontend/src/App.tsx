import { Suspense, lazy, type ComponentType, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Box, CircularProgress } from '@mui/material'
import { AuthProvider } from './context/AuthContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { FeedbackProvider } from './components/feedback'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AppShell } from './components/layout/AppShell'
import { AppThemeProvider } from './theme'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'

// Every page behind login is code-split so each role only downloads the
// screens it can actually open (a Teacher never pays for the DataGrid-heavy
// fee pages, Admin analytics charts load only on the dashboard, etc.).
function lazyPage<K extends string>(loader: () => Promise<Record<K, ComponentType>>, name: K) {
  return lazy(() => loader().then((m) => ({ default: m[name] })))
}
const DashboardPage = lazyPage(() => import('./pages/DashboardPage'), 'DashboardPage')
const StudentsPage = lazyPage(() => import('./pages/StudentsPage'), 'StudentsPage')
const GradesPage = lazyPage(() => import('./pages/GradesPage'), 'GradesPage')
const AdmissionPage = lazyPage(() => import('./pages/AdmissionPage'), 'AdmissionPage')
const FeeVouchersPage = lazyPage(() => import('./pages/FeeVouchersPage'), 'FeeVouchersPage')
const FeeReportsPage = lazyPage(() => import('./pages/FeeReportsPage'), 'FeeReportsPage')
const ExtraChargesPage = lazyPage(() => import('./pages/ExtraChargesPage'), 'ExtraChargesPage')
const AttendancePage = lazyPage(() => import('./pages/AttendancePage'), 'AttendancePage')
const SchoolSettingsPage = lazyPage(() => import('./pages/SchoolSettingsPage'), 'SchoolSettingsPage')
const UserManagementPage = lazyPage(() => import('./pages/UserManagementPage'), 'UserManagementPage')
const BackupPage = lazyPage(() => import('./pages/BackupPage'), 'BackupPage')
const StudentSearchPage = lazyPage(() => import('./pages/StudentSearchPage'), 'StudentSearchPage')
const StudentFeePage = lazyPage(() => import('./pages/StudentFeePage'), 'StudentFeePage')
const PromoteStudentsPage = lazyPage(() => import('./pages/PromoteStudentsPage'), 'PromoteStudentsPage')
const FeeStatusPage = lazyPage(() => import('./pages/FeeStatusPage'), 'FeeStatusPage')
const SchoolsPage = lazyPage(() => import('./pages/SchoolsPage'), 'SchoolsPage')
const ParentManagementPage = lazyPage(() => import('./pages/ParentManagementPage'), 'ParentManagementPage')
const NotificationCenterPage = lazyPage(() => import('./pages/NotificationCenterPage'), 'NotificationCenterPage')
const FeeAuditPage = lazyPage(() => import('./pages/FeeAuditPage'), 'FeeAuditPage')
const CollectionsPage = lazyPage(() => import('./pages/CollectionsPage'), 'CollectionsPage')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function PageLoader() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
      <CircularProgress aria-label="Loading page" />
    </Box>
  )
}

/** Per-route Suspense so the shell (top bar + nav) stays mounted while a
 * lazily-loaded page chunk downloads. */
function s(page: ReactNode) {
  return <Suspense fallback={<PageLoader />}>{page}</Suspense>
}

export default function App() {
  return (
    <AppThemeProvider>
      <ErrorBoundary>
        <FeedbackProvider>
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
                    <Route path="/" element={s(<DashboardPage />)} />

                    <Route element={<ProtectedRoute allowedRoles={['Admin', 'Accountant']} />}>
                      <Route path="/students" element={s(<StudentsPage />)} />
                      <Route path="/students/search" element={s(<StudentSearchPage />)} />
                      <Route path="/students/new" element={s(<AdmissionPage />)} />
                      <Route path="/grades" element={s(<GradesPage />)} />
                      <Route path="/fees/student" element={s(<StudentFeePage />)} />
                      <Route path="/fees/student/:studentId" element={s(<StudentFeePage />)} />
                      <Route path="/fees/vouchers" element={s(<FeeVouchersPage />)} />
                      <Route path="/charges" element={s(<ExtraChargesPage />)} />
                    </Route>

                    <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
                      <Route path="/fees/reports" element={s(<FeeReportsPage />)} />
                      <Route path="/fees/activity" element={s(<FeeAuditPage />)} />
                      <Route path="/fees/collections" element={s(<CollectionsPage />)} />
                      <Route path="/students/promote" element={s(<PromoteStudentsPage />)} />
                      <Route path="/settings" element={s(<SchoolSettingsPage />)} />
                      <Route path="/users" element={s(<UserManagementPage />)} />
                      <Route path="/backup" element={s(<BackupPage />)} />
                      <Route path="/parents" element={s(<ParentManagementPage />)} />
                      {/* Super-admin only — the page itself rejects normal Admins. */}
                      <Route path="/schools" element={s(<SchoolsPage />)} />
                    </Route>

                    {/* Notification Center: Admin (all types) + Accountant (fee reminders). */}
                    <Route element={<ProtectedRoute allowedRoles={['Admin', 'Accountant']} />}>
                      <Route path="/notifications" element={s(<NotificationCenterPage />)} />
                    </Route>

                    <Route element={<ProtectedRoute allowedRoles={['Admin', 'Teacher']} />}>
                      <Route path="/attendance" element={s(<AttendancePage />)} />
                    </Route>

                    <Route element={<ProtectedRoute allowedRoles={['Teacher']} />}>
                      <Route path="/fees/status" element={s(<FeeStatusPage />)} />
                    </Route>

                    <Route path="*" element={<NotFoundPage />} />
                  </Route>
                </Route>
              </Routes>
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
        </FeedbackProvider>
      </ErrorBoundary>
    </AppThemeProvider>
  )
}
