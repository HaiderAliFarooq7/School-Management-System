import { useState } from 'react'
import { Box, Button, Paper, TextField, Typography, Alert } from '@mui/material'
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
  const [error, setError] = useState<string | null>(null)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const role = await login(username, password)
      navigate(role === 'Teacher' ? '/attendance' : '/')
    } catch (err) {
      setError(loginErrorMessage(err))
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.100',
      }}
    >
      <Paper sx={{ p: 4, width: 360 }} elevation={3}>
        <Typography variant="h5" gutterBottom>
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
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
          />
          <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>
            Log In
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}
