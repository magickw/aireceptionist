import * as React from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

export default function HomePage() {
  return (
    <Container maxWidth="lg">
      <Box
        sx={{
          my: 4,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to your AI Receptionist Dashboard
        </Typography>
        <Typography variant="body1">
          Manage your business phone system with the power of AI.
        </Typography>
      </Box>
    </Container>
  );
}

