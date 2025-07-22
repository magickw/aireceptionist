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
          <Link href="/" passHref legacyBehavior>
            <Button color="inherit" component="a">Dashboard</Button>
          </Link>
          <Link href="/business-setup" passHref legacyBehavior>
            <Button color="inherit" component="a">Business</Button>
          </Link>
          <Link href="/call-management" passHref legacyBehavior>
            <Button color="inherit" component="a">Calls</Button>
          </Link>
          <Link href="/call-simulator" passHref legacyBehavior>
            <Button color="inherit" component="a">AI Test</Button>
          </Link>
          <Link href="/integrations" passHref legacyBehavior>
            <Button color="inherit" component="a">Integrations</Button>
          </Link>
          <Link href="/ai-training" passHref legacyBehavior>
            <Button color="inherit" component="a">AI Training</Button>
          </Link>
          <Link href="/customers" passHref legacyBehavior>
            <Button color="inherit" component="a">Customers</Button>
          </Link>
          <Link href="/settings" passHref legacyBehavior>
            <Button color="inherit" component="a">Settings</Button>
          </Link>
          <Button color="inherit" variant="outlined" sx={{ ml: 2, borderColor: 'rgba(255,255,255,0.3)' }}>
            Login
          </Button>
        </Toolbar>
      </AppBar>
    </Box>
  );
}
