'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Container, Box, Typography, TextField, Button, Card, CardContent, Alert, CircularProgress } from '@mui/material';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();

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
        login(response.data.access_token);
      }
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Invalid email or password';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Card sx={{ width: '100%' }}><CardContent sx={{ p: 4 }}>
          <Typography variant="h5" align="center" gutterBottom>Welcome Back</Typography>
          {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
          <Box component="form" onSubmit={handleLogin}>
            <TextField margin="normal" required fullWidth label="Email Address" autoComplete="email" autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />
            <TextField margin="normal" required fullWidth label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button type="submit" fullWidth variant="contained" disabled={loading} sx={{ mt: 3, mb: 2 }}>
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>
          </Box>
        </CardContent></Card>
      </Box>
    </Container>
  );
}
