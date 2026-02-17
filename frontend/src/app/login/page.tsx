'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Container, Box, Typography, TextField, Button, Card, CardContent, Alert, CircularProgress, Divider, Chip } from '@mui/material';
import { Google as GoogleIcon } from '@mui/icons-material';
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
        await login(response.data.access_token);
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
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Card sx={{ width: '100%' }}>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" align="center" gutterBottom>Welcome Back</Typography>
            
            {/* Google Sign In Button */}
            <Button
              fullWidth
              variant="outlined"
              startIcon={googleLoading ? <CircularProgress size={20} /> : <GoogleIcon />}
              onClick={handleGoogleSignIn}
              disabled={googleLoading}
              sx={{ mb: 3, py: 1.5 }}
            >
              Sign in with Google
            </Button>
            
            <Divider sx={{ mb: 3 }}>
              <Chip label="OR" size="small" />
            </Divider>
            
            {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
            
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
              />
              <TextField 
                margin="normal" 
                required 
                fullWidth 
                label="Password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
              />
              <Button 
                type="submit" 
                fullWidth 
                variant="contained" 
                disabled={loading} 
                sx={{ mt: 3, mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Sign In'}
              </Button>
            </Box>
            
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Don't have an account? <Button component="a" href="/register" size="small">Sign up</Button>
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
}
