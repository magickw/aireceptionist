'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress, Grid, Chip, IconButton, Alert } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import api from '@/services/api';

interface OperatingHours {
  [key: string]: { open: string; close: string; closed: boolean };
}

interface BusinessSettings {
  services: string[];
}

export default function BusinessSetupPage() {
  const [profile, setProfile] = useState<{
    id?: number; 
    name: string; 
    type: string;
    phone: string;
    address: string;
    website: string;
    description: string;
    business_license: string;
    operating_hours: OperatingHours;
    settings: BusinessSettings;
  }>({ 
    name: '', 
    type: 'general',
    phone: '',
    address: '',
    website: '',
    description: '',
    business_license: '',
    operating_hours: {
      monday: { open: '09:00', close: '17:00', closed: false },
      tuesday: { open: '09:00', close: '17:00', closed: false },
      wednesday: { open: '09:00', close: '17:00', closed: false },
      thursday: { open: '09:00', close: '17:00', closed: false },
      friday: { open: '09:00', close: '17:00', closed: false },
      saturday: { open: '10:00', close: '14:00', closed: false },
      sunday: { open: '', close: '', closed: true },
    },
    settings: { services: [] }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [newService, setNewService] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/businesses');
        if (res.data.length > 0) {
          const data = res.data[0];
          setProfile({
            ...data,
            operating_hours: data.operating_hours || profile.operating_hours,
            settings: data.settings || { services: [] }
          });
        }
      } catch (error) { 
        console.error('Failed to fetch profile', error); 
      }
      finally { setLoading(false); }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...profile,
        operating_hours: profile.operating_hours,
        settings: profile.settings
      };
      if (profile.id) {
        await api.put(`/businesses/${profile.id}`, payload);
      } else {
        await api.post('/businesses', payload);
      }
      alert('Profile Saved!');
    } catch (error) {
      console.error('Failed to save profile', error);
      alert('Failed to save profile.');
    } finally { setSaving(false); }
  };

  const addService = () => {
    if (newService.trim()) {
      setProfile(p => ({
        ...p,
        settings: { ...p.settings, services: [...p.settings.services, newService.trim()] }
      }));
      setNewService('');
    }
  };

  const removeService = (index: number) => {
    setProfile(p => ({
      ...p,
      settings: { ...p.settings, services: p.settings.services.filter((_: any, i: number) => i !== index) }
    }));
  };

  const updateHours = (day: string, field: string, value: any) => {
    setProfile(p => ({
      ...p,
      operating_hours: {
        ...p.operating_hours,
        [day]: { ...p.operating_hours[day], [field]: value }
      }
    }));
  };

  if (loading) return <Container sx={{p:4}}><LinearProgress/></Container>;

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Business Setup</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure your business information to help the AI assistant understand your business better.
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Basic Information</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Business Name" value={profile.name} onChange={(e) => setProfile(p => ({...p, name: e.target.value}))} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Business Type" value={profile.type} onChange={(e) => setProfile(p => ({...p, type: e.target.value}))} placeholder="e.g., dental, medical, legal" />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Phone Number" value={profile.phone} onChange={(e) => setProfile(p => ({...p, phone: e.target.value}))} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Website" value={profile.website} onChange={(e) => setProfile(p => ({...p, website: e.target.value}))} placeholder="https://" />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth margin="normal" label="Address" value={profile.address} onChange={(e) => setProfile(p => ({...p, address: e.target.value}))} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth margin="normal" label="Business License Number (Optional)" value={profile.business_license} onChange={(e) => setProfile(p => ({...p, business_license: e.target.value}))} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth margin="normal" label="Description" multiline rows={3} value={profile.description} onChange={(e) => setProfile(p => ({...p, description: e.target.value}))} placeholder="Brief description of your business for AI context..." />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Services Offered</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Add the services your business offers. This helps the AI understand what appointments can be booked.
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            {profile.settings.services.map((service: string, index: number) => (
              <Chip key={index} label={service} onDelete={() => removeService(index)} deleteIcon={<DeleteIcon />} />
            ))}
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField size="small" label="Add Service" value={newService} onChange={(e) => setNewService(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addService())} />
            <Button variant="outlined" startIcon={<AddIcon />} onClick={addService}>Add</Button>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Operating Hours</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Set your business hours for each day of the week.
          </Typography>
          {Object.entries(profile.operating_hours).map(([day, hours]) => (
            <Grid container spacing={2} key={day} alignItems="center" sx={{ mb: 1 }}>
              <Grid item xs={12} sm={3}>
                <Typography textTransform="capitalize">{day}</Typography>
              </Grid>
              <Grid item xs={12} sm={2}>
                <TextField size="small" type="time" fullWidth value={hours.open} onChange={(e) => updateHours(day, 'open', e.target.value)} disabled={hours.closed} />
              </Grid>
              <Grid item xs={12} sm={2}>
                <TextField size="small" type="time" fullWidth value={hours.close} onChange={(e) => updateHours(day, 'close', e.target.value)} disabled={hours.closed} />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Button size="small" variant={hours.closed ? "contained" : "outlined"} color={hours.closed ? "error" : "primary"} onClick={() => updateHours(day, 'closed', !hours.closed)}>
                  {hours.closed ? "Closed" : "Open"}
                </Button>
              </Grid>
            </Grid>
          ))}
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button variant="contained" size="large" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Profile'}
        </Button>
      </Box>
    </Container>
  );
}
