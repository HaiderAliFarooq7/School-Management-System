import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel,
  LinearProgress, MenuItem, Radio, RadioGroup, Select, Step, StepLabel, Stepper, Table, TableBody,
  TableCell, TableHead, TableRow, Typography,
} from '@mui/material'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import {
  analyzeImportFile, executeImport, previewImport,
  type AnalyzeResponse, type ExecuteResult, type ImportMode, type PreviewResponse, type PreviewRow,
} from '../api/studentImport'
import { useConfirm } from './feedback'

interface Props {
  open: boolean
  onClose: () => void
}

const STEPS = ['Upload', 'Map Columns', 'Map Classes', 'Import Mode', 'Preview', 'Result']

function apiErrorMessage(e: unknown, fallback: string): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? fallback)
}

export function StudentImportWizard({ open, onClose }: Props) {
  const queryClient = useQueryClient()
  const confirmAction = useConfirm()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null)
  const [mapping, setMapping] = useState<Record<string, string | null>>({})
  const [classMapping, setClassMapping] = useState<Record<string, string>>({})
  const [importMode, setImportMode] = useState<ImportMode>('update_or_add')
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const [result, setResult] = useState<ExecuteResult | null>(null)

  function reset() {
    setStep(0)
    setError(null)
    setAnalysis(null)
    setMapping({})
    setClassMapping({})
    setImportMode('update_or_add')
    setPreview(null)
    setResult(null)
  }

  function handleClose() {
    reset()
    onClose()
  }

  const analyzeMutation = useMutation({
    mutationFn: analyzeImportFile,
    onSuccess: (data) => {
      setAnalysis(data)
      setMapping(data.suggested_mapping)
      setClassMapping(
        Object.fromEntries(
          Object.entries(data.suggested_class_mapping).map(([k, v]) => [k, v ?? '']),
        ),
      )
      setError(null)
      setStep(1)
    },
    onError: (e) => setError(apiErrorMessage(e, 'Could not read this file.')),
  })

  const previewMutation = useMutation({
    mutationFn: () =>
      previewImport({
        raw_rows: analysis!.raw_rows,
        mapping,
        class_value_mapping: classMapping,
        import_mode: importMode,
      }),
    onSuccess: (data) => {
      setPreview(data)
      setError(null)
      setStep(4)
    },
    onError: (e) => setError(apiErrorMessage(e, 'Could not generate preview.')),
  })

  const executeMutation = useMutation({
    mutationFn: () =>
      executeImport({
        raw_rows: analysis!.raw_rows,
        mapping,
        class_value_mapping: classMapping,
        import_mode: importMode,
        only_valid_rows: true,
        confirm_delete_all: importMode === 'delete_all',
      }),
    onSuccess: (data) => {
      setResult(data)
      setError(null)
      setStep(5)
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['class-counts'] })
    },
    onError: (e) => setError(apiErrorMessage(e, 'Import failed.')),
  })

  const allClassesMapped = analysis ? analysis.distinct_class_values.every((v) => classMapping[v]) : false
  const requiredFieldsMapped = Object.values(mapping).includes('name') && Object.values(mapping).includes('class_name')

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Import Students</DialogTitle>
      <DialogContent>
        <Stepper activeStep={step} sx={{ mb: 3 }} alternativeLabel>
          {STEPS.map((label) => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
        </Stepper>

        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

        {step === 0 && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Upload a spreadsheet (.xlsx, .xls, or .csv) of students. Any column layout works — the
              next step lets you map your columns to the right fields, with automatic suggestions.
            </Typography>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              hidden
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) analyzeMutation.mutate(file)
                e.target.value = ''
              }}
            />
            <Button variant="contained" onClick={() => fileInputRef.current?.click()} disabled={analyzeMutation.isPending}>
              {analyzeMutation.isPending ? 'Analyzing…' : 'Choose File'}
            </Button>
            {analyzeMutation.isPending && <LinearProgress sx={{ mt: 2 }} />}
          </Box>
        )}

        {step === 1 && analysis && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {analysis.total_rows} row(s) found. Map each spreadsheet column to a field — columns left
              as "Ignore" won't be imported. <strong>Student Name</strong> and <strong>Class</strong> are required.
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Spreadsheet Column</TableCell>
                  <TableCell>Maps To</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysis.columns.map((col) => (
                  <TableRow key={col}>
                    <TableCell>{col}</TableCell>
                    <TableCell>
                      <Select
                        size="small"
                        fullWidth
                        value={mapping[col] ?? ''}
                        onChange={(e) => setMapping((m) => ({ ...m, [col]: e.target.value || null }))}
                      >
                        <MenuItem value="">— Ignore —</MenuItem>
                        {Object.entries(analysis.available_fields).map(([key, label]) => (
                          <MenuItem key={key} value={key}>{label}</MenuItem>
                        ))}
                      </Select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}

        {step === 2 && analysis && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Your file uses these class names — map each one to a class in this system.
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Spreadsheet Value</TableCell>
                  <TableCell>Maps To</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysis.distinct_class_values.map((val) => (
                  <TableRow key={val}>
                    <TableCell>{val}</TableCell>
                    <TableCell>
                      <Select
                        size="small"
                        fullWidth
                        value={classMapping[val] ?? ''}
                        onChange={(e) => setClassMapping((m) => ({ ...m, [val]: e.target.value }))}
                        displayEmpty
                        error={!classMapping[val]}
                      >
                        <MenuItem value="">— Select a class —</MenuItem>
                        {analysis.known_classes.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
                      </Select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}

        {step === 3 && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Choose how to handle students already in the system.
            </Typography>
            <RadioGroup value={importMode} onChange={(e) => setImportMode(e.target.value as ImportMode)}>
              <FormControlLabel
                value="update_or_add"
                control={<Radio />}
                label="Update existing students (matched by registration number) and add new ones"
              />
              <FormControlLabel value="new_only" control={<Radio />} label="Import only students that don't already exist" />
              <FormControlLabel
                value="delete_all"
                control={<Radio />}
                label="Delete ALL existing students and their records, then import this file"
              />
            </RadioGroup>
            {importMode === 'delete_all' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                This permanently deletes every student, attendance record, fee voucher, extra charge,
                and contact currently in the system before importing. This cannot be undone. Make sure
                you have a backup first.
              </Alert>
            )}
          </Box>
        )}

        {step === 4 && preview && (
          <Box>
            <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
              <Chip label={`Total: ${preview.total_rows}`} />
              <Chip label={`Valid: ${preview.valid_rows}`} color="success" />
              <Chip label={`Invalid: ${preview.invalid_rows}`} color="error" />
              <Chip label={`Duplicate: ${preview.duplicate_rows}`} color="warning" />
              <Chip label={`Missing optional fields: ${preview.missing_fields_rows}`} />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Only valid rows will be imported. Invalid/duplicate rows are listed below for reference.
            </Typography>
            <Box sx={{ height: 350 }}>
              <DataGrid
                rows={preview.rows}
                getRowId={(r: PreviewRow) => r.row_number}
                density="compact"
                columns={[
                  { field: 'row_number', headerName: 'Row', width: 60 },
                  { field: 'name', headerName: 'Name', flex: 1, valueGetter: (_v, r: PreviewRow) => r.data.name ?? '' },
                  { field: 'class_name', headerName: 'Class', width: 100, valueGetter: (_v, r: PreviewRow) => r.data.class_name ?? '' },
                  {
                    field: 'status', headerName: 'Status', width: 100,
                    renderCell: (p) => (
                      <Chip
                        size="small"
                        label={p.value}
                        color={p.value === 'valid' ? 'success' : p.value === 'duplicate' ? 'warning' : 'error'}
                      />
                    ),
                  },
                  { field: 'errors', headerName: 'Notes', flex: 1.5, valueGetter: (_v, r: PreviewRow) => r.errors.join('; ') || r.missing_fields.join(', ') },
                ] as GridColDef<PreviewRow>[]}
              />
            </Box>
          </Box>
        )}

        {step === 5 && result && (
          <Box>
            <Alert severity={result.failed > 0 ? 'warning' : 'success'} sx={{ mb: 2 }}>
              Imported {result.imported}, updated {result.updated}, skipped {result.skipped}, failed {result.failed}.
            </Alert>
            {result.errors.length > 0 && (
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>Row</TableCell><TableCell>Reason</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {result.errors.map((e) => (
                    <TableRow key={e.row_number}><TableCell>{e.row_number}</TableCell><TableCell>{e.reason}</TableCell></TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {step > 0 && step < 4 && <Button onClick={() => setStep((s) => s - 1)}>Back</Button>}
        <Box sx={{ flexGrow: 1 }} />
        <Button onClick={handleClose}>{step === 5 ? 'Close' : 'Cancel'}</Button>
        {step === 1 && (
          <Button variant="contained" disabled={!requiredFieldsMapped} onClick={() => setStep(2)}>Next</Button>
        )}
        {step === 2 && (
          <Button variant="contained" disabled={!allClassesMapped} onClick={() => setStep(3)}>Next</Button>
        )}
        {step === 3 && (
          <Button variant="contained" onClick={() => previewMutation.mutate()} disabled={previewMutation.isPending}>
            {previewMutation.isPending ? 'Checking…' : 'Preview'}
          </Button>
        )}
        {step === 4 && (
          <Button
            variant="contained"
            color={importMode === 'delete_all' ? 'error' : 'primary'}
            disabled={executeMutation.isPending || preview?.valid_rows === 0}
            onClick={async () => {
              const destructive = importMode === 'delete_all'
              const ok = await confirmAction({
                title: destructive ? 'Delete everything and import?' : 'Run import?',
                message: destructive
                  ? `This will permanently delete ALL existing students and their records, then import ${preview?.valid_rows} student(s). This cannot be undone.`
                  : `Import ${preview?.valid_rows} valid student(s)?`,
                confirmLabel: 'Import',
                destructive,
              })
              if (ok) executeMutation.mutate()
            }}
          >
            {executeMutation.isPending ? 'Importing…' : 'Import'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}
