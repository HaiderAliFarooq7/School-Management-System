import { Box, Typography } from '@mui/material'

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {title}
      </Typography>
      <Typography color="text.secondary">
        This module is scheduled for a later build phase — see the project plan.
      </Typography>
    </Box>
  )
}
