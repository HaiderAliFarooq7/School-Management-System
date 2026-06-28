import { useState } from 'react'
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import LogoutIcon from '@mui/icons-material/Logout'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import LockResetIcon from '@mui/icons-material/LockReset'
import { ChangePasswordDialog } from '../ChangePasswordDialog'
import DashboardIcon from '@mui/icons-material/Dashboard'
import PeopleIcon from '@mui/icons-material/People'
import SearchIcon from '@mui/icons-material/Search'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import SchoolIcon from '@mui/icons-material/School'
import ReceiptIcon from '@mui/icons-material/Receipt'
import PaidIcon from '@mui/icons-material/Paid'
import RequestQuoteIcon from '@mui/icons-material/RequestQuote'
import AssessmentIcon from '@mui/icons-material/Assessment'
import NotificationsIcon from '@mui/icons-material/Notifications'
import SettingsIcon from '@mui/icons-material/Settings'
import BackupIcon from '@mui/icons-material/Backup'
import EventAvailableIcon from '@mui/icons-material/EventAvailable'
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import FactCheckIcon from '@mui/icons-material/FactCheck'
import WhatsAppIcon from '@mui/icons-material/WhatsApp'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

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
  { label: 'Communication', path: '/communication', icon: <NotificationsIcon />, roles: ['Admin', 'Accountant'] },
  { label: 'WhatsApp Accounts', path: '/whatsapp-accounts', icon: <WhatsAppIcon />, roles: ['Admin'] },
  { label: 'School Settings', path: '/settings', icon: <SettingsIcon />, roles: ['Admin'] },
  { label: 'Users', path: '/users', icon: <ManageAccountsIcon />, roles: ['Admin'] },
  { label: 'Backup', path: '/backup', icon: <BackupIcon />, roles: ['Admin'] },
]

export function AppShell() {
  const [open, setOpen] = useState(true)
  const [accountMenuAnchor, setAccountMenuAnchor] = useState<null | HTMLElement>(null)
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { role, logout } = useAuth()

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (role && item.roles.includes(role)))

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton color="inherit" edge="start" onClick={() => setOpen(!open)} sx={{ mr: 2 }}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            School Management System
          </Typography>
          <Typography variant="body2" sx={{ mr: 1 }}>
            {role}
          </Typography>
          <IconButton color="inherit" onClick={(e) => setAccountMenuAnchor(e.currentTarget)}>
            <AccountCircleIcon />
          </IconButton>
          <Menu
            anchorEl={accountMenuAnchor}
            open={!!accountMenuAnchor}
            onClose={() => setAccountMenuAnchor(null)}
          >
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
      <Drawer
        variant="persistent"
        open={open}
        sx={{ width: open ? drawerWidth : 0, [`& .MuiDrawer-paper`]: { width: drawerWidth } }}
      >
        <Toolbar />
        <List>
          {visibleItems.map((item) => (
            <ListItemButton
              key={item.path}
              selected={location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Outlet />
      </Box>
    </Box>
  )
}
