'use client';
import { useState } from 'react';
import Link from 'next/link';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Avatar from '@mui/material/Avatar';
import MenuIcon from '@mui/icons-material/Menu';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Divider from '@mui/material/Divider';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme, alpha } from '@mui/material/styles';
import { useAuth } from '@/context/AuthContext';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import Collapse from '@mui/material/Collapse';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PhoneIcon from '@mui/icons-material/Phone';
import HistoryIcon from '@mui/icons-material/History';
import EventIcon from '@mui/icons-material/Event';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import PeopleIcon from '@mui/icons-material/People';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AssessmentIcon from '@mui/icons-material/Assessment';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import WarningIcon from '@mui/icons-material/Warning';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import SchoolIcon from '@mui/icons-material/School';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import RouteIcon from '@mui/icons-material/Route';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ExtensionIcon from '@mui/icons-material/Extension';
import WebhookIcon from '@mui/icons-material/Webhook';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import SmsIcon from '@mui/icons-material/Sms';
import EmailIcon from '@mui/icons-material/Email';
import BusinessIcon from '@mui/icons-material/Business';
import SettingsIcon from '@mui/icons-material/Settings';

const navigationItems = [
  { label: 'Dashboard', href: '/dashboard', icon: <DashboardIcon fontSize="small" /> },
  { label: 'Live Demo', href: '/call-simulator', icon: <PhoneIcon fontSize="small" /> },
  { label: 'Call Logs', href: '/call-logs', icon: <HistoryIcon fontSize="small" /> },
  { label: 'Appointments', href: '/appointments', icon: <EventIcon fontSize="small" /> },
  { label: 'Orders', href: '/orders', icon: <ShoppingCartIcon fontSize="small" /> },
  { label: 'Customers', href: '/customers', icon: <PeopleIcon fontSize="small" /> },
];

const managementItems = [
  { label: 'Analytics', href: '/analytics', icon: <AnalyticsIcon fontSize="small" /> },
  { label: 'Forecasting', href: '/forecasting', icon: <TrendingUpIcon fontSize="small" /> },
  { label: 'Reports', href: '/reports', icon: <AssessmentIcon fontSize="small" /> },
  { label: 'Sentiment', href: '/sentiment', icon: <SentimentSatisfiedIcon fontSize="small" /> },
  { label: 'Churn Prediction', href: '/churn', icon: <WarningIcon fontSize="small" /> },
  { label: 'Pricing', href: '/pricing', icon: <AttachMoneyIcon fontSize="small" /> },
];

const aiItems = [
  { label: 'Knowledge Base', href: '/knowledge-base', icon: <LibraryBooksIcon fontSize="small" /> },
  { label: 'AI Training', href: '/ai-training', icon: <SchoolIcon fontSize="small" /> },
  { label: 'AI Approvals', href: '/approvals', icon: <CheckCircleIcon fontSize="small" /> },
  { label: 'Voice Greetings', href: '/voice-greetings', icon: <RecordVoiceOverIcon fontSize="small" /> },
  { label: 'Call Routing', href: '/call-routing', icon: <RouteIcon fontSize="small" /> },
  { label: 'Chatbot', href: '/chatbot', icon: <SmartToyIcon fontSize="small" /> },
];

const integrationItems = [
  { label: 'Integrations', href: '/integrations', icon: <ExtensionIcon fontSize="small" /> },
  { label: 'Webhooks', href: '/webhooks', icon: <WebhookIcon fontSize="small" /> },
  { label: 'Calendar', href: '/calendar', icon: <CalendarTodayIcon fontSize="small" /> },
  { label: 'SMS', href: '/sms', icon: <SmsIcon fontSize="small" /> },
  { label: 'Email', href: '/email', icon: <EmailIcon fontSize="small" /> },
];

const systemItems = [
  { label: 'Business Setup', href: '/business-setup', icon: <BusinessIcon fontSize="small" /> },
  { label: 'Settings', href: '/settings', icon: <SettingsIcon fontSize="small" /> },
];

export default function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    management: true,
    ai: true,
    integrations: true,
    system: false,
  });
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, isAuthenticated, logout } = useAuth();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleSection = (section: string) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const renderNavItem = (item: { label: string; href: string; icon?: React.ReactNode }, onClick?: () => void) => (
    <ListItem key={item.label} disablePadding>
      <ListItemButton
        component={Link}
        href={item.href}
        onClick={onClick}
        sx={{
          py: 1,
          px: 2,
          borderRadius: 2,
          mx: 1,
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: alpha(theme.palette.primary.main, 0.08),
          },
        }}
      >
        {item.icon && (
          <ListItemIcon sx={{ minWidth: 36, color: 'text.secondary' }}>
            {item.icon}
          </ListItemIcon>
        )}
        <ListItemText primary={item.label} primaryTypographyProps={{ fontWeight: 500 }} />
      </ListItemButton>
    </ListItem>
  );

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'left', height: '100%' }}>
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: 'primary.main', display: 'flex', alignItems: 'center', gap: 1 }}>
          <PhoneIcon />
          Receptium
        </Typography>
      </Box>
      <List sx={{ py: 2 }}>
        {!isAuthenticated && (
          <>
            {renderNavItem({ label: 'Home', href: '/' }, handleDrawerToggle)}
            {renderNavItem({ label: 'Demo', href: '/call-simulator', icon: <PhoneIcon fontSize="small" /> }, handleDrawerToggle)}
            <Divider sx={{ my: 1 }} />
          </>
        )}
        {isAuthenticated && (
          <>
            {/* Main Navigation */}
            {navigationItems.map((item) => renderNavItem(item, handleDrawerToggle))}
            <Divider sx={{ my: 1 }} />

            {/* Management Section */}
            <ListItem button onClick={() => toggleSection('management')} sx={{ py: 1.5, px: 2 }}>
              <ListItemText primary="Management" sx={{ '& .MuiTypography-root': { fontWeight: 700 } }} />
              {openSections.management ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.management} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {managementItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>

            {/* AI & Automation Section */}
            <ListItem button onClick={() => toggleSection('ai')} sx={{ py: 1.5, px: 2 }}>
              <ListItemText primary="AI & Automation" sx={{ '& .MuiTypography-root': { fontWeight: 700 } }} />
              {openSections.ai ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.ai} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {aiItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>

            {/* Integrations Section */}
            <ListItem button onClick={() => toggleSection('integrations')} sx={{ py: 1.5, px: 2 }}>
              <ListItemText primary="Integrations" sx={{ '& .MuiTypography-root': { fontWeight: 700 } }} />
              {openSections.integrations ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.integrations} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {integrationItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>

            {/* System Section */}
            <ListItem button onClick={() => toggleSection('system')} sx={{ py: 1.5, px: 2 }}>
              <ListItemText primary="System" sx={{ '& .MuiTypography-root': { fontWeight: 700 } }} />
              {openSections.system ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.system} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {systemItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>
          </>
        )}
        <Divider sx={{ my: 1 }} />
        {isAuthenticated ? (
          <>
            <ListItem sx={{ py: 2, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%' }}>
                <Avatar sx={{ width: 36, height: 36, bgcolor: 'primary.main' }}>
                  <AccountCircleIcon />
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {user?.name || user?.email?.split('@')[0]}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user?.email}
                  </Typography>
                </Box>
              </Box>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton onClick={logout} sx={{ py: 1.5, px: 2, color: 'error.main' }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Logout" />
              </ListItemButton>
            </ListItem>
          </>
        ) : (
          <ListItem disablePadding>
            <ListItemButton component={Link} href="/login" sx={{ py: 1.5, px: 2 }}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                <AccountCircleIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Login" />
            </ListItemButton>
          </ListItem>
        )}
      </List>
    </Box>
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar
        position="static"
        elevation={1}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box
            component={Link}
            href={isAuthenticated ? '/dashboard' : '/'}
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              textDecoration: 'none',
              cursor: 'pointer',
            }}
          >
            <PhoneIcon sx={{ mr: 1, fontSize: { xs: 20, sm: 24 } }} />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 800,
                color: 'inherit',
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
                letterSpacing: '-0.5px',
              }}
            >
              Receptium
            </Typography>
          </Box>

          {/* Desktop Navigation */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 0.5, alignItems: 'center' }}>
            {!isAuthenticated && (
              <>
                <Button
                  color="inherit"
                  component={Link}
                  href="/"
                  sx={{
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    px: 1.5,
                    py: 0.75,
                    borderRadius: 10,
                    minWidth: 'auto',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.15)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  Home
                </Button>
                <Button
                  color="inherit"
                  component={Link}
                  href="/call-simulator"
                  sx={{
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    px: 1.5,
                    py: 0.75,
                    borderRadius: 10,
                    minWidth: 'auto',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.15)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  Demo
                </Button>
              </>
            )}

            {isAuthenticated && (
              <>
                {/* Primary Nav Items */}
                {navigationItems.map((item) => (
                  <Button
                    key={item.label}
                    color="inherit"
                    component={Link}
                    href={item.href}
                    sx={{
                      textTransform: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      px: 1.5,
                      py: 0.75,
                      borderRadius: 10,
                      minWidth: 'auto',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        bgcolor: 'rgba(255,255,255,0.15)',
                        transform: 'translateY(-1px)',
                      },
                    }}
                  >
                    {item.label}
                  </Button>
                ))}

                {/* More Menu */}
                <Button
                  color="inherit"
                  onClick={handleMenuOpen}
                  sx={{
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    px: 1.5,
                    py: 0.75,
                    borderRadius: 10,
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.15)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  More
                </Button>
                <Menu
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleMenuClose}
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                  PaperProps={{
                    sx: {
                      mt: 1,
                      minWidth: 220,
                      maxHeight: '80vh',
                      overflowY: 'auto',
                      boxShadow: '0 10px 40px -10px rgba(0, 0, 0, 0.2)',
                      borderRadius: 2,
                    }
                  }}
                >
                  <MenuItem
                    disabled
                    sx={{
                      fontWeight: 700,
                      color: 'primary.main',
                      fontSize: '0.8rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    Management
                  </MenuItem>
                  {managementItems.map((item) => (
                    <MenuItem
                      key={item.label}
                      component={Link}
                      href={item.href}
                      onClick={handleMenuClose}
                      sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
                    >
                      {item.icon}
                      {item.label}
                    </MenuItem>
                  ))}

                  <Divider sx={{ my: 1 }} />

                  <MenuItem
                    disabled
                    sx={{
                      fontWeight: 700,
                      color: 'primary.main',
                      fontSize: '0.8rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    AI & Automation
                  </MenuItem>
                  {aiItems.map((item) => (
                    <MenuItem
                      key={item.label}
                      component={Link}
                      href={item.href}
                      onClick={handleMenuClose}
                      sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
                    >
                      {item.icon}
                      {item.label}
                    </MenuItem>
                  ))}
                  <Divider sx={{ my: 1 }} />
                  <MenuItem
                    disabled
                    sx={{
                      fontWeight: 700,
                      color: 'primary.main',
                      fontSize: '0.8rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    Integrations
                  </MenuItem>
                  {integrationItems.map((item) => (
                    <MenuItem
                      key={item.label}
                      component={Link}
                      href={item.href}
                      onClick={handleMenuClose}
                      sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
                    >
                      {item.icon}
                      {item.label}
                    </MenuItem>
                  ))}
                  <Divider sx={{ my: 1 }} />
                  <MenuItem
                    disabled
                    sx={{
                      fontWeight: 700,
                      color: 'primary.main',
                      fontSize: '0.8rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    System
                  </MenuItem>
                  {systemItems.map((item) => (
                    <MenuItem
                      key={item.label}
                      component={Link}
                      href={item.href}
                      onClick={handleMenuClose}
                      sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
                    >
                      {item.icon}
                      {item.label}
                    </MenuItem>
                  ))}
                </Menu>
              </>
            )}

            {isAuthenticated ? (
              <Box sx={{ display: 'flex', alignItems: 'center', ml: 2, gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Avatar sx={{ width: 36, height: 36, bgcolor: 'rgba(255,255,255,0.2)' }}>
                    <AccountCircleIcon />
                  </Avatar>
                  <Box sx={{ display: { xs: 'none', md: 'block' } }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                      {user?.name || user?.email?.split('@')[0]}
                    </Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.7rem' }}>
                      {user?.email?.split('@')[0]}@{user?.email?.split('@')[1]}
                    </Typography>
                  </Box>
                </Box>
                <IconButton
                  color="inherit"
                  onClick={logout}
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.15)',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.25)',
                      transform: 'rotate(180deg)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                  size="small"
                  title="Logout"
                >
                  <LogoutIcon fontSize="small" />
                </IconButton>
              </Box>
            ) : (
              <Button
                color="inherit"
                variant="outlined"
                component={Link}
                href="/login"
                sx={{
                  ml: 2,
                  borderColor: 'rgba(255,255,255,0.4)',
                  borderRadius: 12,
                  textTransform: 'none',
                  fontWeight: 600,
                  px: 3,
                  py: 0.75,
                  borderWidth: 1.5,
                  '&:hover': {
                    borderColor: 'rgba(255,255,255,0.8)',
                    bgcolor: 'rgba(255,255,255,0.1)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 14px 0 rgba(0, 0, 0, 0.15)',
                  },
                }}
              >
                Login
              </Button>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile Navigation Drawer */}
      <Drawer
        variant="temporary"
        anchor="left"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: 280,
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          },
        }}
      >
        {drawer}
      </Drawer>
    </Box>
  );
}
