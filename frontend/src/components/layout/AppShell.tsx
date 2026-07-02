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
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { ChangePasswordDialog } from '../ChangePasswordDialog'
import { useAuth } from '../../context/AuthContext'
import { useColorMode } from '../../theme'

const drawerWidth = 250

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
  roles?: string[]
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <DashboardIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Students', path: '/students', icon: <PeopleIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Advanced Search', path: '/students/search', icon: <SearchIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'New Admission', path: '/students/new', icon: <PersonAddIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Grades', path: '/grades', icon: <SchoolIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Promote Students', path: '/students/promote', icon: <TrendingUpIcon />, roles: ['Admin'] },
  { label: 'Student Fee', path: '/fees/student', icon: <PaidIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Fee Vouchers', path: '/fees/vouchers', icon: <ReceiptIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Fee Reports', path: '/fees/reports', icon: <AssessmentIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Extra Charges', path: '/charges', icon: <RequestQuoteIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'Attendance', path: '/attendance', icon: <EventAvailableIcon />, roles: ['Admin', 'Teacher'] },
  { label: 'Fee Status', path: '/fees/status', icon: <FactCheckIcon />, roles: ['Teacher'] },
  { label: 'School Settings', path: '/settings', icon: <SettingsIcon />, roles: ['Admin'] },
  { label: 'Users', path: '/users', icon: <ManageAccountsIcon />, roles: ['Admin'] },
  { label: 'Backup', path: '/backup', icon: <BackupIcon />, roles: ['Admin'] },
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
  const { role, logout } = useAuth()
  const { mode, toggle: toggleColorMode } = useColorMode()

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (role && item.roles.includes(role)))

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
            School Management System
          </Typography>
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
