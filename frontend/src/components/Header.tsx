import Link from 'next/link';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';

export default function Header() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #1e40af 100%)' }}>
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            AI Receptionist Pro
          </Typography>
          <Button color="inherit" component={Link} href="/">Dashboard</Button>
          <Button color="inherit" component={Link} href="/business-setup">Business</Button>
          <Button color="inherit" component={Link} href="/call-management">Calls</Button>
          <Button color="inherit" component={Link} href="/call-simulator">AI Test</Button>
          <Button color="inherit" component={Link} href="/integrations">Integrations</Button>
          <Button color="inherit" component={Link} href="/ai-training">AI Training</Button>
          <Button color="inherit" component={Link} href="/customers">Customers</Button>
          <Button color="inherit" component={Link} href="/settings">Settings</Button>
          <Button color="inherit" variant="outlined" sx={{ ml: 2, borderColor: 'rgba(255,255,255,0.3)' }}>
            Login
          </Button>
        </Toolbar>
      </AppBar>
    </Box>
  );
}
