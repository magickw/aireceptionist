'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress } from '@mui/material';
import api from '@/services/api';

export default function BusinessSetupPage() {
  const [profile, setProfile] = useState<{id?: number; name: string; industry: string}>({ name: '', industry: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/businesses');
        if (res.data.length > 0) setProfile(res.data[0]);
      } catch (error) { console.error('Failed to fetch profile', error); }
      finally { setLoading(false); }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    try {
      setLoading(true);
      if (profile.id) {  // Check for ID to determine if update or create
        await api.put(`/businesses/${profile.id}`, profile);
      } else {
        await api.post('/businesses', profile);
      }
      alert('Profile Saved!');
    } catch (error) {
      console.error('Failed to save profile', error);
      alert('Failed to save profile.');
    } finally { setLoading(false); }
  };

  if (loading) return <Container sx={{p:4}}><LinearProgress/></Container>;

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Business Setup</Typography>
      <Card><CardContent>
        <TextField fullWidth margin="normal" label="Business Name" value={profile.name} onChange={(e) => setProfile(p => ({...p, name: e.target.value}))} />
        <TextField fullWidth margin="normal" label="Industry" value={profile.industry} onChange={(e) => setProfile(p => ({...p, industry: e.target.value}))} />
        <Button variant="contained" sx={{ mt: 2 }} onClick={handleSave} disabled={loading}>Save Profile</Button>
      </CardContent></Card>
    </Container>
  );
}
