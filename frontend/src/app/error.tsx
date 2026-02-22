'use client';

import { Box, Button, Typography, Container } from '@mui/material';
import Link from 'next/link';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          gap: 3,
        }}
      >
        <Typography variant="h4" color="error">
          Something went wrong
        </Typography>
        
        <Typography variant="body1" color="text.secondary">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={reset}>
            Try Again
          </Button>
          
          <Button variant="outlined" component={Link} href="/">
            Go to Dashboard
          </Button>
        </Box>
        
        {error.digest && (
          <Typography variant="caption" color="text.disabled">
            Error ID: {error.digest}
          </Typography>
        )}
      </Box>
    </Container>
  );
}