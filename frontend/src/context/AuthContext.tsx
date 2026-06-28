import { createContext, useContext, useState, type ReactNode } from 'react'
import { login as apiLogin } from '../api/auth'

interface AuthState {
  isAuthenticated: boolean
  role: string | null
  assignedClassName: string | null
  login: (username: string, password: string) => Promise<string>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<string | null>(localStorage.getItem('sms_role'))
  const [assignedClassName, setAssignedClassName] = useState<string | null>(
    localStorage.getItem('sms_assigned_class'),
  )

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    localStorage.setItem('sms_token', res.access_token)
    localStorage.setItem('sms_role', res.role)
    if (res.assigned_class_name) {
      localStorage.setItem('sms_assigned_class', res.assigned_class_name)
    }
    setRole(res.role)
    setAssignedClassName(res.assigned_class_name)
    return res.role
  }

  function logout() {
    localStorage.removeItem('sms_token')
    localStorage.removeItem('sms_role')
    localStorage.removeItem('sms_assigned_class')
    setRole(null)
    setAssignedClassName(null)
  }

  return (
    <AuthContext.Provider
      value={{ isAuthenticated: !!role, role, assignedClassName, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
