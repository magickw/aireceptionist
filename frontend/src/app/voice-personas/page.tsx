'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, 
  Button, TextField, Slider, CircularProgress, Alert,
  Avatar, Chip, Radio, RadioGroup, FormControlLabel,
  FormControl, FormLabel, Divider
} from '@mui/material';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SaveIcon from '@mui/icons-material/Save';
import api from '@/services/api';

interface Persona {
  name: string;
  description: string;
  language: string;
  gender?: string;
}

export default function VoicePersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [currentPersona, setCurrentPersona] = useState<string>('professional');
  const [loading, setLoading] = useState(true);
  const [previewing, setLoadingPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pitch, setPitch] = useState(0);
  const [speed, setSpeed] = useState(1.0);
  const [sampleText, setSampleText] = useState('Hello! I am your AI receptionist. How can I help you today?');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [availableRes, currentRes] = await Promise.all([
        api.get('/voice-personas/available'),
        api.get('/voice-personas/current')
      ]);
      
      setPersonas(availableRes.data.personas);
      if (currentRes.data.persona) {
        setCurrentPersona(currentRes.data.persona.name);
        setPitch(currentRes.data.persona.pitch || 0);
        setSpeed(currentRes.data.persona.speed || 1.0);
      }
    } catch (err) {
      setError('Failed to load voice personas.');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    try {
      setLoadingPreview(true);
      const response = await api.post('/voice-personas/preview', {
        text: sampleText,
        persona_name: currentPersona
      });
      
      const audio = new Audio(`data:${response.data.content_type};base64,${response.data.audio_base64}`);
      audio.play();
    } catch (err) {
      setError('Failed to generate preview.');
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');
      await api.post('/voice-personas/set', {
        persona_name: currentPersona,
        customizations: { pitch, speed }
      });
      setSuccess('Voice persona saved successfully!');
    } catch (err) {
      setError('Failed to save persona.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Container sx={{ mt: 4 }}><CircularProgress /></Container>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={800} gutterBottom>
          AI Voice Persona
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Customize how your AI receptionist sounds to your customers.
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

      <Grid container spacing={4}>
        {/* Selection */}
        <Grid item xs={12} md={7}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>Select a Voice</Typography>
              <RadioGroup 
                value={currentPersona} 
                onChange={(e) => setCurrentPersona(e.target.value)}
              >
                <Grid container spacing={2}>
                  {personas.map((p) => (
                    <Grid item xs={12} sm={6} key={p.name}>
                      <Box 
                        sx={{ 
                          p: 2, 
                          border: '1px solid', 
                          borderColor: currentPersona === p.name ? 'primary.main' : 'divider',
                          borderRadius: 2,
                          bgcolor: currentPersona === p.name ? 'primary.50' : 'transparent',
                          cursor: 'pointer'
                        }}
                        onClick={() => setCurrentPersona(p.name)}
                      >
                        <FormControlLabel 
                          value={p.name} 
                          control={<Radio />} 
                          label={
                            <Box>
                              <Typography variant="subtitle2" fontWeight="bold">{p.name.charAt(0).toUpperCase() + p.name.slice(1)}</Typography>
                              <Typography variant="caption" color="text.secondary">{p.description}</Typography>
                            </Box>
                          } 
                        />
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </RadioGroup>

              <Divider sx={{ my: 4 }} />

              <Typography variant="h6" gutterBottom>Voice Fine-Tuning</Typography>
              <Box sx={{ px: 2 }}>
                <Typography gutterBottom>Pitch ({pitch > 0 ? '+' : ''}{pitch}%)</Typography>
                <Slider 
                  value={pitch} 
                  onChange={(_, v) => setPitch(v as number)} 
                  min={-20} max={20} step={1}
                  sx={{ mb: 3 }}
                />
                
                <Typography gutterBottom>Speed ({speed}x)</Typography>
                <Slider 
                  value={speed} 
                  onChange={(_, v) => setSpeed(v as number)} 
                  min={0.5} max={2.0} step={0.1}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Preview & Save */}
        <Grid item xs={12} md={5}>
          <Card variant="outlined" sx={{ position: 'sticky', top: 24 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Test Your Voice</Typography>
              <TextField
                fullWidth
                multiline
                rows={4}
                value={sampleText}
                onChange={(e) => setSampleText(e.target.value)}
                placeholder="Enter text for the AI to say..."
                sx={{ mb: 3 }}
              />
              <Button
                fullWidth
                variant="outlined"
                startIcon={previewing ? <CircularProgress size={20} /> : <PlayArrowIcon />}
                onClick={handlePreview}
                disabled={previewing || !sampleText}
                sx={{ mb: 2 }}
              >
                Listen to Sample
              </Button>
              <Button
                fullWidth
                variant="contained"
                startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                onClick={handleSave}
                disabled={saving}
              >
                Save Persona
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}
