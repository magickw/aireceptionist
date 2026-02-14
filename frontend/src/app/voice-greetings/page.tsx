'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Grid, Alert, CircularProgress, Chip, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { RecordVoiceOver, Add } from '@mui/icons-material';
import { voiceGreetingsApi } from '@/services/api';

export default function VoiceGreetingsPage() {
  const [loading, setLoading] = useState(true);
  const [greetings, setGreetings] = useState<any[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', greeting_type: 'welcome', text: '' });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [greetRes, typesRes] = await Promise.all([
        voiceGreetingsApi.list(),
        voiceGreetingsApi.getTypes()
      ]);
      setGreetings(greetRes.data.greetings || []);
      setTypes(typesRes.data.types || []);
    } catch (error) { console.error('Failed to fetch', error); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.text) return;
    try {
      await voiceGreetingsApi.create(formData);
      setDialogOpen(false);
      setFormData({ name: '', greeting_type: 'welcome', text: '' });
      fetchData();
    } catch (error) { alert('Failed to create'); }
  };

  const handleActivate = async (greetingType: string) => {
    try {
      await voiceGreetingsApi.update(greetingType, { is_active: true });
      fetchData();
    } catch (error) { alert('Failed to update'); }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Voice Greetings</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
          Add Greeting
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Customize voice greetings for different call scenarios.
      </Typography>

      {loading ? <CircularProgress /> : (
        <Grid container spacing={3}>
          {types.map((type) => {
            const greeting = greetings.find((g) => g.type === type);
            return (
              <Grid item xs={12} md={6} key={type}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>{type}</Typography>
                      {greeting?.is_active && <Chip label="Active" color="success" size="small" />}
                    </Box>
                    {greeting ? (
                      <>
                        <Typography variant="body2" color="text.secondary">{greeting.text}</Typography>
                        {!greeting.is_active && (
                          <Button size="small" onClick={() => handleActivate(type)} sx={{ mt: 1 }}>
                            Set as Active
                          </Button>
                        )}
                      </>
                    ) : (
                      <Alert severity="info">No greeting configured</Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Voice Greeting</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} sx={{ mt: 2, mb: 2 }} />
          <TextField fullWidth select SelectProps={{ native: true }} label="Type" value={formData.greeting_type} 
            onChange={(e) => setFormData({ ...formData, greeting_type: e.target.value })} sx={{ mb: 2 }}>
            {types.map((t) => <option key={t} value={t}>{t}</option>)}
          </TextField>
          <TextField fullWidth multiline rows={3} label="Greeting Text" value={formData.text} 
            onChange={(e) => setFormData({ ...formData, text: e.target.value })} 
            placeholder="Thank you for calling..." />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Create</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
