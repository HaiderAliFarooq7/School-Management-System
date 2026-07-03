import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  Typography, useMediaQuery, useTheme,
} from '@mui/material'
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner'
import { useNavigate } from 'react-router-dom'
import jsQR from 'jsqr'
import { listStudents } from '../api/students'

/** Minimal typing for the native BarcodeDetector (Chrome/Edge/Android).
 * Where it's missing (Firefox, older Safari) we decode frames with jsQR. */
interface BarcodeDetectorLike {
  detect(source: CanvasImageSource): Promise<{ rawValue: string }[]>
}
declare global {
  interface Window {
    BarcodeDetector?: new (options?: { formats: string[] }) => BarcodeDetectorLike
  }
}

/** Extracts a student id from whatever a fee-challan QR contains.
 * New challans: https://<app>/fees/student/123?v=456 — parse the path.
 * Old printed challans: "REG-0001|January 2026|1500.00|Unpaid|VC-12" —
 * resolve the registration number to a student via the search API. */
async function resolveStudentId(text: string): Promise<number | null> {
  const urlMatch = text.match(/\/fees\/student\/(\d+)/)
  if (urlMatch) return Number(urlMatch[1])

  const legacyMatch = text.match(/^(REG-\d+)\|/)
  if (legacyMatch) {
    const students = await listStudents({ search: legacyMatch[1] })
    const exact = students.find((s) => s.registration_no === legacyMatch[1])
    return exact?.student_id ?? null
  }
  return null
}

interface Props {
  open: boolean
  onClose: () => void
}

/** Live camera scanner for fee-challan QR codes: point the webcam/phone
 * camera at a printed challan and it opens that student's fee page. */
export function QrScannerDialog({ open, onClose }: Props) {
  const theme = useTheme()
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'))
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const stopScanRef = useRef(false)
  const [error, setError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [status, setStatus] = useState('Point the camera at the QR code on a fee challan.')

  const stopCamera = useCallback(() => {
    stopScanRef.current = true
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }, [])

  const handleClose = useCallback(() => {
    stopCamera()
    onClose()
  }, [stopCamera, onClose])

  useEffect(() => {
    if (!open) return
    let cancelled = false
    stopScanRef.current = false
    setError(null)
    setStarting(true)
    setStatus('Point the camera at the QR code on a fee challan.')

    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('This browser does not support camera access. Use a recent Chrome, Edge, Safari, or Firefox.')
        setStarting(false)
        return
      }
      try {
        // Prefer the back camera on phones; laptops fall back to the webcam.
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        const video = videoRef.current
        if (!video) return
        video.srcObject = stream
        await video.play()
        setStarting(false)
        scanLoop()
      } catch (e) {
        const name = (e as DOMException)?.name
        setError(
          name === 'NotAllowedError'
            ? 'Camera permission was denied. Allow camera access for this site and try again.'
            : name === 'NotFoundError'
              ? 'No camera was found on this device.'
              : 'Could not start the camera. Close other apps using it and try again.',
        )
        setStarting(false)
      }
    }

    const detector = window.BarcodeDetector ? new window.BarcodeDetector({ formats: ['qr_code'] }) : null

    async function decodeFrame(): Promise<string | null> {
      const video = videoRef.current
      if (!video || video.readyState < 2) return null
      if (detector) {
        try {
          const codes = await detector.detect(video)
          return codes[0]?.rawValue ?? null
        } catch {
          /* fall through to jsQR below */
        }
      }
      const canvas = canvasRef.current
      if (!canvas) return null
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      if (!ctx || !canvas.width) return null
      ctx.drawImage(video, 0, 0)
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      return jsQR(imageData.data, imageData.width, imageData.height)?.data ?? null
    }

    async function scanLoop() {
      while (!stopScanRef.current && !cancelled) {
        const text = await decodeFrame()
        if (text) {
          setStatus('QR code detected — looking up the student…')
          try {
            const studentId = await resolveStudentId(text)
            if (studentId) {
              stopCamera()
              handleCloseRef.current()
              navigate(`/fees/student/${studentId}`)
              return
            }
            setStatus("That QR isn't a fee challan from this system. Keep scanning…")
          } catch {
            setStatus('Could not look up that student — check your connection and rescan.')
          }
          // Brief pause so the same frame doesn't re-trigger instantly.
          await new Promise((r) => setTimeout(r, 1200))
        } else {
          await new Promise((r) => setTimeout(r, 200))
        }
      }
    }

    start()
    return () => {
      cancelled = true
      stopCamera()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // Keep the latest close handler available to the scan loop without
  // restarting the camera when it changes.
  const handleCloseRef = useRef(handleClose)
  useEffect(() => {
    handleCloseRef.current = handleClose
  }, [handleClose])

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth fullScreen={fullScreen}>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <QrCodeScannerIcon /> Scan Fee Challan QR
      </DialogTitle>
      <DialogContent>
        {error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <Box sx={{ position: 'relative' }}>
            <Box
              component="video"
              ref={videoRef}
              muted
              playsInline
              sx={{
                width: '100%',
                maxHeight: { xs: '60vh', sm: 420 },
                borderRadius: 2,
                bgcolor: 'common.black',
                objectFit: 'cover',
              }}
            />
            {starting && (
              <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CircularProgress />
              </Box>
            )}
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
              {status}
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
