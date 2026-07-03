import { useEffect, useState } from 'react'
import { useMediaQuery, useTheme } from '@mui/material'
import type { GridColumnVisibilityModel } from '@mui/x-data-grid'

/**
 * DataGrid props that hide the given secondary columns on phone-width
 * screens, so the essential columns and the row Actions stay visible without
 * hunting through horizontal scroll. On wider screens all columns show.
 * Users can still toggle columns manually via the column menu — the model is
 * controlled state, re-seeded only when crossing the breakpoint.
 *
 * Usage: <DataGrid {...usePhoneColumns(['father_name', 'phone'])} ... />
 */
export function usePhoneColumns(hiddenOnPhone: string[]) {
  const theme = useTheme()
  const isPhone = useMediaQuery(theme.breakpoints.down('sm'))
  const hiddenKey = hiddenOnPhone.join(',')
  const [model, setModel] = useState<GridColumnVisibilityModel>({})

  useEffect(() => {
    setModel(
      isPhone
        ? Object.fromEntries(hiddenKey.split(',').filter(Boolean).map((f) => [f, false]))
        : {},
    )
  }, [isPhone, hiddenKey])

  return { columnVisibilityModel: model, onColumnVisibilityModelChange: setModel }
}
