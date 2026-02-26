'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Container, Box, Typography, TextField, Button, Card, CardContent, Alert, CircularProgress, Divider, Chip, useTheme, alpha } from '@mui/material';
import { Google as GoogleIcon, LockOutlined, EmailOutlined } from '@mui/icons-material';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const router = useRouter();
  const { login, isAuthenticated, signInWithGoogle } = useAuth();
  const theme = useTheme();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      console.log('Attempting login with:', email);
      const response = await api.post('/auth/login', { email, password });
      console.log('Login response:', response.data);
      if (response.data.access_token) {
        await login(response.data);
      }
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Invalid email or password';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setGoogleLoading(true);
    try {
      await signInWithGoogle();
    } catch (err: any) {
      console.error('Google sign-in error:', err);
      const errorMessage = err.message || 'Google sign-in failed';
      setError(errorMessage);
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Card
          sx={{
            width: '100%',
            boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.1)',
            borderRadius: 3,
            border: '1px solid rgba(226, 232, 240, 0.8)',
          }}
        >
          <CardContent sx={{ p: { xs: 3, sm: 4, md: 5 } }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Typography
                variant="h4"
                gutterBottom
                sx={{
                  fontWeight: 800,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Welcome Back
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to continue to Receptium
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            {/* Google Sign In Button */}
            <Button
              fullWidth
              variant="outlined"
              startIcon={googleLoading ? <CircularProgress size={20} /> : <GoogleIcon />}
              onClick={handleGoogleSignIn}
              disabled={googleLoading}
              sx={{
                mb: 3,
                py: 1.75,
                borderRadius: 2,
                fontWeight: 600,
                borderWidth: 1.5,
                textTransform: 'none',
                fontSize: '0.95rem',
              }}
            >
              Continue with Google
            </Button>

            <Divider sx={{ mb: 3 }}>
              <Chip label="or sign in with email" size="small" sx={{ fontWeight: 500 }} />
            </Divider>

            <Box component="form" onSubmit={handleLogin}>
              <TextField
                margin="normal"
                required
                fullWidth
                label="Email Address"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                InputProps={{
                  startAdornment: <EmailOutlined sx={{ mr: 1.5, color: 'text.secondary' }} />,
                }}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="Password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                InputProps={{
                  startAdornment: <LockOutlined sx={{ mr: 1.5, color: 'text.secondary' }} />,
                }}
                sx={{ mb: 3 }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  py: 1.75,
                  borderRadius: 2,
                  fontWeight: 600,
                  textTransform: 'none',
                  fontSize: '1rem',
                  boxShadow: '0 4px 14px 0 rgba(37, 99, 235, 0.39)',
                  '&:hover': {
                    boxShadow: '0 6px 20px 0 rgba(37, 99, 235, 0.23)',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
              </Button>
            </Box>

            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{' '}
                <Button
                  component="a"
                  href="/register"
                  size="small"
                  sx={{ fontWeight: 600, textTransform: 'none' }}
                >
                  Sign up
                </Button>
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
