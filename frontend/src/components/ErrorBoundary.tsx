import { Component, type ReactNode } from 'react'
import { Box, Button, Paper, Typography } from '@mui/material'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'

interface State {
  hasError: boolean
  errorId: string | null
}

/** Last-resort catch for rendering errors anywhere in the app — shows a
 * friendly recovery screen instead of a blank white page. The error id ties
 * a user's report to the console log entry. */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false, errorId: null }

  static getDerivedStateFromError(): Partial<State> {
    return { hasError: true, errorId: `ERR-${Date.now().toString(36).toUpperCase()}` }
  }

  componentDidCatch(error: unknown, info: unknown) {
    console.error(`[${this.state.errorId}] Unhandled render error:`, error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', p: 2 }}>
        <Paper sx={{ p: 4, maxWidth: 440, textAlign: 'center' }}>
          <ErrorOutlineIcon color="error" sx={{ fontSize: 48, mb: 1 }} />
          <Typography variant="h6" component="h1" gutterBottom>
            Something went wrong
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 1 }}>
            An unexpected error occurred. Reloading usually fixes it — your data is safe.
          </Typography>
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mb: 2 }}>
            Error ID: {this.state.errorId}
          </Typography>
          <Button variant="contained" onClick={() => window.location.reload()}>
            Reload App
          </Button>
        </Paper>
      </Box>
    )
  }
}
