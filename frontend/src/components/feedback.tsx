import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Snackbar,
  type AlertColor,
} from '@mui/material'

export interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
  /** Renders the confirm button in the error color and focuses Cancel. */
  destructive?: boolean
}

interface FeedbackApi {
  showToast: (message: string, severity?: AlertColor) => void
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const FeedbackContext = createContext<FeedbackApi | null>(null)

/** Success/error toasts. Replaces native alert(). */
export function useToast() {
  const ctx = useContext(FeedbackContext)
  if (!ctx) throw new Error('useToast must be used within FeedbackProvider')
  return ctx.showToast
}

/** Promise-based confirmation dialog. Replaces native confirm(). */
export function useConfirm() {
  const ctx = useContext(FeedbackContext)
  if (!ctx) throw new Error('useConfirm must be used within FeedbackProvider')
  return ctx.confirm
}

interface ToastState {
  key: number
  message: string
  severity: AlertColor
}

export function FeedbackProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null)
  const [confirmState, setConfirmState] = useState<ConfirmOptions | null>(null)
  const confirmResolver = useRef<((ok: boolean) => void) | null>(null)

  const showToast = useCallback((message: string, severity: AlertColor = 'success') => {
    setToast({ key: Date.now(), message, severity })
  }, [])

  const confirm = useCallback((options: ConfirmOptions) => {
    setConfirmState(options)
    return new Promise<boolean>((resolve) => {
      confirmResolver.current = resolve
    })
  }, [])

  const closeConfirm = useCallback((ok: boolean) => {
    setConfirmState(null)
    confirmResolver.current?.(ok)
    confirmResolver.current = null
  }, [])

  const api = useMemo(() => ({ showToast, confirm }), [showToast, confirm])

  return (
    <FeedbackContext.Provider value={api}>
      {children}

      <Snackbar
        key={toast?.key}
        open={!!toast}
        autoHideDuration={4000}
        onClose={(_, reason) => reason !== 'clickaway' && setToast(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={toast?.severity ?? 'success'}
          variant="filled"
          onClose={() => setToast(null)}
          sx={{ width: '100%' }}
        >
          {toast?.message}
        </Alert>
      </Snackbar>

      <Dialog open={!!confirmState} onClose={() => closeConfirm(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{confirmState?.title}</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ whiteSpace: 'pre-line' }}>{confirmState?.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => closeConfirm(false)} autoFocus={confirmState?.destructive}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={confirmState?.destructive ? 'error' : 'primary'}
            onClick={() => closeConfirm(true)}
          >
            {confirmState?.confirmLabel ?? 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>
    </FeedbackContext.Provider>
  )
}
