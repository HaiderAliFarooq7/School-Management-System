import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Alert, Box, Button, CircularProgress, Divider, Typography } from '@mui/material'
import { importStudents, resetDatabase, restoreBackup, runBackup } from '../api/backup'
import { downloadFile } from '../api/client'

export function BackupPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const restoreInputRef = useRef<HTMLInputElement>(null)
  const [message, setMessage] = useState<{ text: string; severity: 'success' | 'error' } | null>(null)
  const [confirmReset, setConfirmReset] = useState(false)

  const backupMutation = useMutation({
    mutationFn: runBackup,
    onSuccess: () => setMessage({ text: 'Backup downloaded to your computer.', severity: 'success' }),
    onError: () => setMessage({ text: 'Backup failed — check that pg_dump is on the server PATH.', severity: 'error' }),
  })

  const restoreMutation = useMutation({
    mutationFn: (file: File) => restoreBackup(file),
    onSuccess: (res) => setMessage({ text: res.detail, severity: 'success' }),
    onError: () => setMessage({ text: 'Restore failed — make sure you selected a valid .dump backup file.', severity: 'error' }),
  })

  const importMutation = useMutation({
    mutationFn: (file: File) => importStudents(file),
    onSuccess: (res) => setMessage({ text: `Imported/updated ${res.imported} student(s).`, severity: 'success' }),
    onError: () => setMessage({ text: 'Import failed — check the file format.', severity: 'error' }),
  })

  const resetMutation = useMutation({
    mutationFn: resetDatabase,
    onSuccess: () => {
      setMessage({ text: 'All operational data has been reset.', severity: 'success' })
      setConfirmReset(false)
    },
    onError: () => setMessage({ text: 'Reset failed.', severity: 'error' }),
  })

  return (
    <Box sx={{ maxWidth: 600 }}>
      <Typography variant="h5" gutterBottom>
        Backup &amp; Restore
      </Typography>
      {message && <Alert severity={message.severity} sx={{ mb: 2 }}>{message.text}</Alert>}

      <Typography variant="h6" gutterBottom>
        Database Backup &amp; Restore
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Backups download straight to your computer and are never stored on the server. Keep them
        somewhere safe — you'll need the .dump file to restore.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          onClick={() => backupMutation.mutate()}
          disabled={backupMutation.isPending}
          startIcon={backupMutation.isPending ? <CircularProgress size={18} color="inherit" /> : undefined}
        >
          {backupMutation.isPending ? 'Preparing…' : 'Download Backup'}
        </Button>
        <Button
          variant="outlined"
          color="warning"
          onClick={() => restoreInputRef.current?.click()}
          disabled={restoreMutation.isPending}
          startIcon={restoreMutation.isPending ? <CircularProgress size={18} color="inherit" /> : undefined}
        >
          {restoreMutation.isPending ? 'Restoring…' : 'Restore from Backup'}
        </Button>
        <input
          ref={restoreInputRef}
          type="file"
          accept=".dump"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file && confirm('Restoring will overwrite ALL current data with the backup. Continue?')) {
              restoreMutation.mutate(file)
            }
            e.target.value = ''
          }}
        />
      </Box>

      <Divider sx={{ mb: 3 }} />

      <Typography variant="h6" gutterBottom>
        Excel Export / Import (Students)
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button variant="outlined" onClick={() => downloadFile('/backup/export-students.xlsx', {}, 'students_export.xlsx')}>
          Export Students to Excel
        </Button>
        <Button variant="outlined" onClick={() => fileInputRef.current?.click()}>
          Import Students from Excel
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) importMutation.mutate(file)
          }}
        />
      </Box>

      <Divider sx={{ mb: 3 }} />

      <Typography variant="h6" gutterBottom color="error">
        Danger Zone
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Permanently deletes all students, vouchers, charges, contacts, and notification history.
        School settings, roles, and user accounts are kept. Run a backup first.
      </Typography>
      {!confirmReset ? (
        <Button color="error" variant="outlined" onClick={() => setConfirmReset(true)}>
          Reset All Data
        </Button>
      ) : (
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="error" variant="contained" onClick={() => resetMutation.mutate()}>
            Confirm Reset — This Cannot Be Undone
          </Button>
          <Button onClick={() => setConfirmReset(false)}>Cancel</Button>
        </Box>
      )}
    </Box>
  )
}
