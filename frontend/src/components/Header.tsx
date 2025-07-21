import Link from 'next/link';

export default function Header() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI Receptionist
          </Typography>
          <Link href="/analytics" passHref legacyBehavior>
            <Button color="inherit" component="a">Analytics</Button>
          </Link>
          <Link href="/appointments" passHref legacyBehavior>
            <Button color="inherit" component="a">Appointments</Button>
          </Link>
          <Link href="/call-logs" passHref legacyBehavior>
            <Button color="inherit" component="a">Call Logs</Button>
          </Link>
          <Link href="/settings" passHref legacyBehavior>
            <Button color="inherit" component="a">Settings</Button>
          </Link>
          <Button color="inherit">Login</Button>
        </Toolbar>
      </AppBar>
    </Box>
  );
}
