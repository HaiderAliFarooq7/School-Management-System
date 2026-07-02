import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ThemeProvider, createTheme, CssBaseline, useMediaQuery } from '@mui/material'

type ColorMode = 'light' | 'dark'

const STORAGE_KEY = 'sms_color_mode'

const ColorModeContext = createContext<{ mode: ColorMode; toggle: () => void }>({
  mode: 'light',
  toggle: () => {},
})

export function useColorMode() {
  return useContext(ColorModeContext)
}

/** Uses a system font stack instead of shipping webfonts — keeps the bundle
 * small and renders with each platform's native UI font (Segoe UI, SF, Roboto). */
const FONT_STACK =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'

function buildTheme(mode: ColorMode) {
  return createTheme({
    palette:
      mode === 'light'
        ? {
            mode,
            primary: { main: '#1565c0' },
            secondary: { main: '#7b1fa2' },
            background: { default: '#f4f6f9', paper: '#ffffff' },
          }
        : {
            mode,
            primary: { main: '#90caf9' },
            secondary: { main: '#ce93d8' },
            background: { default: '#10151c', paper: '#161d26' },
          },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily: FONT_STACK,
      h5: { fontWeight: 700 },
      h6: { fontWeight: 600 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiCard: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: ({ theme }) => ({
            border: `1px solid ${theme.palette.divider}`,
          }),
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: mode === 'dark' ? { backgroundImage: 'none', backgroundColor: '#161d26' } : {},
        },
      },
      MuiTableHead: {
        styleOverrides: {
          root: ({ theme }) => ({
            '& .MuiTableCell-head': { fontWeight: 600, backgroundColor: theme.palette.action.hover },
          }),
        },
      },
    },
  })
}

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)')
  const [mode, setMode] = useState<ColorMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'dark' || stored === 'light' ? stored : prefersDark ? 'dark' : 'light'
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  const value = useMemo(
    () => ({ mode, toggle: () => setMode((m) => (m === 'light' ? 'dark' : 'light')) }),
    [mode],
  )
  const theme = useMemo(() => buildTheme(mode), [mode])

  return (
    <ColorModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  )
}
