'use client';

import { useEffect } from 'react';
import { Box, Typography, Button, Container } from '@mui/material';

export const dynamic = 'force-dynamic';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
          gap: 2
        }}
      >
        <Typography variant="h3" color="error" gutterBottom>
          Something went wrong!
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          We apologize for the inconvenience. An unexpected error has occurred.
        </Typography>
        <Button
          variant="contained"
          onClick={() => reset()}
          sx={{ mt: 2 }}
        >
          Try again
        </Button>
      </Box>
    </Container>
  );
}
