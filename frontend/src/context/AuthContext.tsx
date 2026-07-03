import { createContext, useContext, useState, type ReactNode } from 'react'
import { login as apiLogin, type LoginResponse } from '../api/auth'

export interface SchoolIdentity {
  schoolId: number | null
  schoolName: string
  campusName: string
}

interface AuthState {
  isAuthenticated: boolean
  role: string | null
  assignedClassName: string | null
  isSuper: boolean
  school: SchoolIdentity
  login: (username: string, password: string) => Promise<string>
  /** Applies a re-issued token (super admin switching schools). */
  applySession: (res: LoginResponse) => void
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

function readSchool(): SchoolIdentity {
  const raw = localStorage.getItem('sms_school_id')
  return {
    schoolId: raw ? Number(raw) : null,
    schoolName: localStorage.getItem('sms_school_name') ?? '',
    campusName: localStorage.getItem('sms_campus_name') ?? '',
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<string | null>(localStorage.getItem('sms_role'))
  const [assignedClassName, setAssignedClassName] = useState<string | null>(
    localStorage.getItem('sms_assigned_class'),
  )
  const [isSuper, setIsSuper] = useState<boolean>(localStorage.getItem('sms_is_super') === '1')
  const [school, setSchool] = useState<SchoolIdentity>(readSchool)

  function applySession(res: LoginResponse) {
    localStorage.setItem('sms_token', res.access_token)
    localStorage.setItem('sms_role', res.role)
    if (res.assigned_class_name) {
      localStorage.setItem('sms_assigned_class', res.assigned_class_name)
    } else {
      localStorage.removeItem('sms_assigned_class')
    }
    localStorage.setItem('sms_is_super', res.is_super ? '1' : '0')
    if (res.school_id != null) {
      localStorage.setItem('sms_school_id', String(res.school_id))
      localStorage.setItem('sms_school_name', res.school_name ?? '')
      localStorage.setItem('sms_campus_name', res.campus_name ?? '')
    } else {
      localStorage.removeItem('sms_school_id')
      localStorage.removeItem('sms_school_name')
      localStorage.removeItem('sms_campus_name')
    }
    setRole(res.role)
    setAssignedClassName(res.assigned_class_name)
    setIsSuper(!!res.is_super)
    setSchool({
      schoolId: res.school_id ?? null,
      schoolName: res.school_name ?? '',
      campusName: res.campus_name ?? '',
    })
  }

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    applySession(res)
    return res.role
  }

  function logout() {
    for (const key of [
      'sms_token', 'sms_role', 'sms_assigned_class',
      'sms_is_super', 'sms_school_id', 'sms_school_name', 'sms_campus_name',
    ]) {
      localStorage.removeItem(key)
    }
    setRole(null)
    setAssignedClassName(null)
    setIsSuper(false)
    setSchool({ schoolId: null, schoolName: '', campusName: '' })
  }

  return (
    <AuthContext.Provider
      value={{ isAuthenticated: !!role, role, assignedClassName, isSuper, school, login, applySession, logout }}
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
