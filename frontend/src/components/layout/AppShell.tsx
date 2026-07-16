import { useState } from 'react'
import {
  AppBar,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import LogoutIcon from '@mui/icons-material/Logout'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import LockResetIcon from '@mui/icons-material/LockReset'
import DarkModeIcon from '@mui/icons-material/DarkMode'
import LightModeIcon from '@mui/icons-material/LightMode'
import DashboardIcon from '@mui/icons-material/Dashboard'
import PeopleIcon from '@mui/icons-material/People'
import SearchIcon from '@mui/icons-material/Search'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import SchoolIcon from '@mui/icons-material/School'
import ReceiptIcon from '@mui/icons-material/Receipt'
import PaidIcon from '@mui/icons-material/Paid'
import RequestQuoteIcon from '@mui/icons-material/RequestQuote'
import AssessmentIcon from '@mui/icons-material/Assessment'
import SettingsIcon from '@mui/icons-material/Settings'
import BackupIcon from '@mui/icons-material/Backup'
import EventAvailableIcon from '@mui/icons-material/EventAvailable'
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import FactCheckIcon from '@mui/icons-material/FactCheck'
import CorporateFareIcon from '@mui/icons-material/CorporateFare'
import FamilyRestroomIcon from '@mui/icons-material/FamilyRestroom'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import HistoryIcon from '@mui/icons-material/History'
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { listSchools, switchSchool } from '../../api/master'
import { ChangePasswordDialog } from '../ChangePasswordDialog'
import { useToast } from '../feedback'
import { useAuth } from '../../context/AuthContext'
import { useColorMode } from '../../theme'

const drawerWidth = 250

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
  roles?: string[]
  superOnly?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <DashboardIcon />, roles: ['Admin', 'Accountant', 'Teacher'] },
  { label: 'Students', path: '/students', icon: <PeopleIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Advanced Search', path: '/students/search', icon: <SearchIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'New Admission', path: '/students/new', icon: <PersonAddIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Grades', path: '/grades', icon: <SchoolIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Promote Students', path: '/students/promote', icon: <TrendingUpIcon />, roles: ['Admin'] },
  { label: 'Student Fee', path: '/fees/student', icon: <PaidIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Fee Vouchers', path: '/fees/vouchers', icon: <ReceiptIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Fee Reports', path: '/fees/reports', icon: <AssessmentIcon />, roles: ['Admin'] },
  { label: 'Fee Activity', path: '/fees/activity', icon: <HistoryIcon />, roles: ['Admin'] },
  { label: 'Collections', path: '/fees/collections', icon: <AccountBalanceWalletIcon />, roles: ['Admin'] },
  { label: 'Extra Charges', path: '/charges', icon: <RequestQuoteIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Attendance', path: '/attendance', icon: <EventAvailableIcon />, roles: ['Admin', 'Teacher', 'Accountant'] },
  { label: 'Fee Status', path: '/fees/status', icon: <FactCheckIcon />, roles: ['Admin', 'Accountant', 'Teacher'] },
  { label: 'Parents', path: '/parents', icon: <FamilyRestroomIcon />, roles: ['Admin'] },
  { label: 'Notifications', path: '/notifications', icon: <NotificationsActiveIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'School Settings', path: '/settings', icon: <SettingsIcon />, roles: ['Admin'] },
  { label: 'Users', path: '/users', icon: <ManageAccountsIcon />, roles: ['Admin'] },
  { label: 'Backup', path: '/backup', icon: <BackupIcon />, roles: ['Admin'] },
  { label: 'Schools', path: '/schools', icon: <CorporateFareIcon />, superOnly: true },
]

export function AppShell() {
  const theme = useTheme()
  // Phones and small tablets get an overlay drawer that closes after
  // navigating; wider screens keep the persistent collapsible sidebar.
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const [desktopOpen, setDesktopOpen] = useState(true)
  const [accountMenuAnchor, setAccountMenuAnchor] = useState<null | HTMLElement>(null)
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { role, logout, isSuper, school } = useAuth()
  const { mode, toggle: toggleColorMode } = useColorMode()

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.superOnly) return isSuper
    return !item.roles || (role && item.roles.includes(role))
  })
  const title = school.schoolName
    ? `${school.schoolName}${school.campusName ? ` — ${school.campusName}` : ''}`
    : 'School Management System'

  function handleNavigate(path: string) {
    navigate(path)
    if (isMobile) setMobileOpen(false)
  }

  const navList = (
    <List component="nav" aria-label="Main navigation" sx={{ px: 1 }}>
      {visibleItems.map((item) => (
        <ListItemButton
          key={item.path}
          selected={location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)}
          onClick={() => handleNavigate(item.path)}
          sx={{ borderRadius: 2, mb: 0.25 }}
        >
          <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
          <ListItemText primary={item.label} />
        </ListItemButton>
      ))}
    </List>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            aria-label="Toggle navigation menu"
            onClick={() => (isMobile ? setMobileOpen(!mobileOpen) : setDesktopOpen(!desktopOpen))}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="h1" noWrap sx={{ flexGrow: 1, minWidth: 0 }}>
            {title}
          </Typography>
          {isSuper && <SchoolSwitcher />}
          {role && (
            <Chip
              label={role}
              size="small"
              sx={{ mr: 1, color: 'inherit', borderColor: 'currentColor', display: { xs: 'none', sm: 'inline-flex' } }}
              variant="outlined"
            />
          )}
          <Tooltip title={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
            <IconButton color="inherit" aria-label="Toggle dark mode" onClick={toggleColorMode}>
              {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
          </Tooltip>
          <IconButton
            color="inherit"
            aria-label="Account menu"
            onClick={(e) => setAccountMenuAnchor(e.currentTarget)}
          >
            <AccountCircleIcon />
          </IconButton>
          <Menu
            anchorEl={accountMenuAnchor}
            open={!!accountMenuAnchor}
            onClose={() => setAccountMenuAnchor(null)}
          >
            {role && (
              <MenuItem disabled sx={{ display: { sm: 'none' }, opacity: '1 !important' }}>
                <Typography variant="body2" color="text.secondary">Signed in as {role}</Typography>
              </MenuItem>
            )}
            <MenuItem onClick={() => { setPasswordDialogOpen(true); setAccountMenuAnchor(null) }}>
              <ListItemIcon><LockResetIcon fontSize="small" /></ListItemIcon>
              Change Password
            </MenuItem>
            <MenuItem onClick={() => { setAccountMenuAnchor(null); logout(); navigate('/login') }}>
              <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <ChangePasswordDialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)} />

      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ [`& .MuiDrawer-paper`]: { width: drawerWidth } }}
        >
          <Toolbar>
            <Typography variant="subtitle1" fontWeight={600}>Menu</Typography>
          </Toolbar>
          <Divider />
          {navList}
        </Drawer>
      ) : (
        <Drawer
          variant="persistent"
          open={desktopOpen}
          sx={{
            width: desktopOpen ? drawerWidth : 0,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth },
          }}
        >
          <Toolbar />
          {navList}
        </Drawer>
      )}

      <Box
        component="main"
        sx={{ flexGrow: 1, p: { xs: 2, sm: 3 }, mt: 8, minWidth: 0, overflowX: 'hidden' }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}

/** Super-admin only: jump between schools from anywhere. Re-issues the JWT
 * pinned to the selected school and reloads all data for it. */
function SchoolSwitcher() {
  const { school, applySession } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)
  const { data: schools } = useQuery({ queryKey: ['master-schools'], queryFn: listSchools, staleTime: 60_000 })

  const mutation = useMutation({
    mutationFn: (id: number) => switchSchool(id),
    onSuccess: (session) => {
      applySession(session)
      queryClient.clear()
      toast(`Now managing ${session.school_name}${session.campus_name ? ` — ${session.campus_name}` : ''}.`)
      navigate('/')
    },
    onError: () => toast('Could not switch school.', 'error'),
  })

  const switchable = (schools ?? []).filter((s) => s.database_status !== 'archived')

  return (
    <>
      <Tooltip title="Switch school">
        <IconButton color="inherit" aria-label="Switch school" onClick={(e) => setAnchor(e.currentTarget)}>
          <CorporateFareIcon />
        </IconButton>
      </Tooltip>
      <Menu anchorEl={anchor} open={!!anchor} onClose={() => setAnchor(null)}>
        {switchable.map((s) => (
          <MenuItem
            key={s.school_id}
            selected={s.school_id === school.schoolId}
            onClick={() => { setAnchor(null); if (s.school_id !== school.schoolId) mutation.mutate(s.school_id) }}
          >
            {s.school_name}{s.campus_name ? ` — ${s.campus_name}` : ''}
          </MenuItem>
        ))}
        {switchable.length === 0 && <MenuItem disabled>No schools</MenuItem>}
      </Menu>
    </>
  )
}
