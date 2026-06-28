import { useEffect, useState } from 'react'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, Switch, TextField, Typography,
} from '@mui/material'
import type { Provider } from '../api/communication'

interface Props {
  open: boolean
  onClose: () => void
  provider: Provider | null
  onSave: (values: { enabled: boolean; configuration_json: Record<string, string> }) => void
  onTest: () => void
  testResult?: string | null
  error?: string | null
}

export function ProviderDialog({ open, onClose, provider, onSave, onTest, testResult, error }: Props) {
  const [enabled, setEnabled] = useState(false)
  const [configText, setConfigText] = useState('{}')

  useEffect(() => {
    if (provider) {
      setEnabled(provider.enabled)
      setConfigText(JSON.stringify(provider.configuration_json, null, 2))
    }
  }, [provider])

  if (!provider) return null

  const configError = (() => {
    try {
      JSON.parse(configText)
      return null
    } catch {
      return 'Configuration JSON is invalid.'
    }
  })()

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{provider.name}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Placeholder implementation ({provider.type}) — sends return mock success until a real gateway is wired in.
          Only one provider may be active at a time; enabling this one disables any other.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {testResult && <Alert severity="info" sx={{ mb: 2 }}>{testResult}</Alert>}
        <FormControlLabel
          control={<Switch checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />}
          label="Enabled"
          sx={{ mb: 2, display: 'block' }}
        />
        <TextField
          fullWidth
          multiline
          minRows={6}
          label="Configuration JSON"
          value={configText}
          onChange={(e) => setConfigText(e.target.value)}
          error={!!configError}
          helperText={configError}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onTest}>Test Provider</Button>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={!!configError}
          onClick={() => onSave({ enabled, configuration_json: JSON.parse(configText) })}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  )
}
