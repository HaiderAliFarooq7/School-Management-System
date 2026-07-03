import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  InputAdornment,
  Paper,
  TextField,
  Typography,
} from '@mui/material'
import Visibility from '@mui/icons-material/Visibility'
import VisibilityOff from '@mui/icons-material/VisibilityOff'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function loginErrorMessage(err: unknown): string {
  const e = err as { response?: { status?: number; data?: { detail?: string } }; request?: unknown; message?: string }
  if (e.response) {
    // The backend responded — show its actual reason (e.g. "Invalid username or password").
    return e.response.data?.detail ?? `Login failed (HTTP ${e.response.status}).`
  }
  if (e.request) {
    // Request went out but got no response — wrong API URL, CORS block, or backend down.
    return 'Could not reach the server. Please check your connection or try again shortly.'
  }
  return e.message ?? 'Login failed. Please try again.'
}

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const role = await login(username, password)
      navigate(role === 'Teacher' ? '/attendance' : '/')
    } catch (err) {
      setError(loginErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100dvh',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      <Paper sx={{ p: { xs: 3, sm: 4 }, width: '100%', maxWidth: 380 }} elevation={3}>
        <Typography variant="h5" component="h1" gutterBottom>
          School Management System
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Sign in to continue
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
            autoFocus
            autoComplete="username"
          />
          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            autoComplete="current-password"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword((v) => !v)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />
          <Button
            fullWidth
            variant="contained"
            type="submit"
            size="large"
            disabled={submitting || !username || !password}
            startIcon={submitting ? <CircularProgress size={18} color="inherit" /> : undefined}
            sx={{ mt: 2 }}
          >
            {submitting ? 'Signing in…' : 'Log In'}
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}
