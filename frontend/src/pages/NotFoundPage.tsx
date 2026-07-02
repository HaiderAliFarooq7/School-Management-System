import { Box, Button, Typography } from '@mui/material'
import SearchOffIcon from '@mui/icons-material/SearchOff'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        gap: 2,
        p: 3,
      }}
    >
      <SearchOffIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
      <Typography variant="h5" component="h1">
        Page not found
      </Typography>
      <Typography color="text.secondary">
        The page you're looking for doesn't exist or may have moved.
      </Typography>
      <Button variant="contained" component={Link} to="/">
        Go to Dashboard
      </Button>
    </Box>
  )
}
