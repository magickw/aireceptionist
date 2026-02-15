'use client';
import { useState } from 'react';
import Link from 'next/link';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useAuth } from '@/context/AuthContext';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import Collapse from '@mui/material/Collapse';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';

const navigationItems = [
  { label: 'Dashboard', href: '/', icon: 'dashboard' },
  { label: 'Live Demo', href: '/call-simulator', icon: 'phone' },
  { label: 'Call Management', href: '/call-management', icon: 'settings' },
  { label: 'Call Logs', href: '/call-logs', icon: 'history' },
  { label: 'Appointments', href: '/appointments', icon: 'event' },
  { label: 'Customers', href: '/customers', icon: 'people' },
];

const managementItems = [
  { label: 'Analytics', href: '/analytics', icon: 'chart' },
  { label: 'Forecasting', href: '/forecasting', icon: 'trending' },
  { label: 'Reports', href: '/reports', icon: 'assessment' },
  { label: 'Sentiment', href: '/sentiment', icon: 'sentiment' },
  { label: 'Churn Prediction', href: '/churn', icon: 'warning' },
  { label: 'Pricing', href: '/pricing', icon: 'attach_money' },
];

const aiItems = [
  { label: 'Knowledge Base', href: '/knowledge-base', icon: 'library' },
  { label: 'AI Training', href: '/ai-training', icon: 'school' },
  { label: 'Voice Greetings', href: '/voice-greetings', icon: 'record' },
  { label: 'Call Routing', href: '/call-routing', icon: 'route' },
  { label: 'Chatbot', href: '/chatbot', icon: 'bot' },
];

const integrationItems = [
  { label: 'Integrations', href: '/integrations', icon: 'extension' },
  { label: 'Webhooks', href: '/webhooks', icon: 'webhook' },
  { label: 'Calendar', href: '/calendar', icon: 'calendar' },
  { label: 'SMS', href: '/sms', icon: 'sms' },
  { label: 'Email', href: '/email', icon: 'email' },
];

const systemItems = [
  { label: 'Business Setup', href: '/business-setup', icon: 'business' },
  { label: 'Settings', href: '/settings', icon: 'settings' },
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

  const renderNavItem = (item: { label: string; href: string }, onClick?: () => void) => (
    <ListItem key={item.label} disablePadding>
      <ListItemButton 
        component={Link} 
        href={item.href} 
        onClick={onClick}
        sx={{ textAlign: 'center', py: 1 }}
      >
        <ListItemText primary={item.label} />
      </ListItemButton>
    </ListItem>
  );

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
      <Typography variant="h6" sx={{ my: 2, fontWeight: 'bold', color: 'primary.main' }}>
        Nova Voice Agent
      </Typography>
      <Divider />
      <List>
        {isAuthenticated && (
          <>
            {/* Main Navigation */}
            {navigationItems.map((item) => renderNavItem(item, handleDrawerToggle))}
            <Divider sx={{ my: 1 }} />
            
            {/* Management Section */}
            <ListItem button onClick={() => toggleSection('management')} sx={{ justifyContent: 'center', py: 1 }}>
              <ListItemText primary="Management" sx={{ '& .MuiTypography-root': { fontWeight: 'bold' } }} />
              {openSections.management ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.management} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {managementItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>
            
            {/* AI & Automation Section */}
            <ListItem button onClick={() => toggleSection('ai')} sx={{ justifyContent: 'center', py: 1 }}>
              <ListItemText primary="AI & Automation" sx={{ '& .MuiTypography-root': { fontWeight: 'bold' } }} />
              {openSections.ai ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.ai} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {aiItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>
            
            {/* Integrations Section */}
            <ListItem button onClick={() => toggleSection('integrations')} sx={{ justifyContent: 'center', py: 1 }}>
              <ListItemText primary="Integrations" sx={{ '& .MuiTypography-root': { fontWeight: 'bold' } }} />
              {openSections.integrations ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={openSections.integrations} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {integrationItems.map((item) => renderNavItem(item, handleDrawerToggle))}
              </List>
            </Collapse>
            
            {/* System Section */}
            <ListItem button onClick={() => toggleSection('system')} sx={{ justifyContent: 'center', py: 1 }}>
              <ListItemText primary="System" sx={{ '& .MuiTypography-root': { fontWeight: 'bold' } }} />
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
            <ListItem sx={{ justifyContent: 'center', py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountCircleIcon color="primary" />
                <Typography variant="body2">{user?.name || user?.email}</Typography>
              </Box>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton onClick={logout} sx={{ textAlign: 'center', color: 'error.main' }}>
                <ListItemText primary="Logout" />
              </ListItemButton>
            </ListItem>
          </>
        ) : (
          <ListItem disablePadding>
            <ListItemButton component={Link} href="/login" sx={{ textAlign: 'center' }}>
              <ListItemText primary="Login" />
            </ListItemButton>
          </ListItem>
        )}
      </List>
    </Box>
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #1e40af 100%)' }}>
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
          <Typography 
            variant="h6" 
            component={Link} 
            href="/" 
            sx={{ 
              flexGrow: 1, 
              fontWeight: 'bold', 
              textDecoration: 'none', 
              color: 'inherit', 
              cursor: 'pointer',
              fontSize: { xs: '1rem', sm: '1.25rem' }
            }}
          >
            Nova Voice Agent
          </Typography>
          
          {/* Desktop Navigation */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 0.5, alignItems: 'center' }}>
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
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      px: 1.5,
                      py: 1,
                      borderRadius: '8px',
                      minWidth: 'auto',
                      '&:hover': {
                        bgcolor: 'rgba(255,255,255,0.15)',
                      }
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
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    px: 1.5,
                    borderRadius: '8px',
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
                    sx: { mt: 1, minWidth: 200 }
                  }}
                >
                  <MenuItem disabled sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    Management
                  </MenuItem>
                  {managementItems.map((item) => (
                    <MenuItem key={item.label} component={Link} href={item.href} onClick={handleMenuClose}>
                      {item.label}
                    </MenuItem>
                  ))}
                  <MenuItem disabled sx={{ fontWeight: 'bold', color: 'primary.main', mt: 1 }}>
                    AI & Automation
                  </MenuItem>
                  {aiItems.map((item) => (
                    <MenuItem key={item.label} component={Link} href={item.href} onClick={handleMenuClose}>
                      {item.label}
                    </MenuItem>
                  ))}
                  <MenuItem disabled sx={{ fontWeight: 'bold', color: 'primary.main', mt: 1 }}>
                    Integrations
                  </MenuItem>
                  {integrationItems.map((item) => (
                    <MenuItem key={item.label} component={Link} href={item.href} onClick={handleMenuClose}>
                      {item.label}
                    </MenuItem>
                  ))}
                  <MenuItem disabled sx={{ fontWeight: 'bold', color: 'primary.main', mt: 1 }}>
                    System
                  </MenuItem>
                  {systemItems.map((item) => (
                    <MenuItem key={item.label} component={Link} href={item.href} onClick={handleMenuClose}>
                      {item.label}
                    </MenuItem>
                  ))}
                </Menu>
              </>
            )}
            
            {isAuthenticated ? (
              <Box sx={{ display: 'flex', alignItems: 'center', ml: 2, gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountCircleIcon sx={{ fontSize: 24, opacity: 0.9 }} />
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {user?.name || user?.email?.split('@')[0]}
                  </Typography>
                </Box>
                <IconButton 
                  color="inherit" 
                  onClick={logout}
                  sx={{ 
                    bgcolor: 'rgba(255,255,255,0.1)',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' }
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
                  borderColor: 'rgba(255,255,255,0.3)',
                  borderRadius: '10px',
                  textTransform: 'none',
                  fontWeight: 600,
                  px: 3,
                  '&:hover': {
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                  }
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
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
      >
        {drawer}
      </Drawer>
    </Box>
  );
}
