'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Grid, Alert, CircularProgress, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  IconButton, Tooltip, Snackbar, Divider, Paper
} from '@mui/material';
import { 
  RecordVoiceOver as VoiceIcon, 
  Add as AddIcon, 
  Edit as EditIcon, 
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Check as CheckIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { voiceGreetingsApi } from '@/services/api';

const GREETING_TYPE_INFO: Record<string, { label: string; description: string }> = {
  welcome: { label: 'Welcome', description: 'Played when a customer first calls' },
  after_hours: { label: 'After Hours', description: 'Played when calling outside business hours' },
  voicemail: { label: 'Voicemail', description: 'Played when directing to voicemail' },
  hold: { label: 'Hold', description: 'Played while customer is on hold' },
  transfer: { label: 'Transfer', description: 'Played before transferring to an agent' },
  goodbye: { label: 'Goodbye', description: 'Played at the end of the call' },
};

export default function VoiceGreetingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [greetings, setGreetings] = useState<any[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: '', greeting_type: 'welcome', text: '', language: 'en' });
  const [editData, setEditData] = useState({ text: '' });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [greetRes, typesRes] = await Promise.all([
        voiceGreetingsApi.list(),
        voiceGreetingsApi.getTypes()
      ]);
      setGreetings(greetRes.data.greetings || []);
      setTypes(typesRes.data.types || []);
    } catch (error) { 
      console.error('Failed to fetch', error);
      showSnackbar('Failed to load greetings', 'error');
    }
    finally { setLoading(false); }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.text) {
      showSnackbar('Please fill in all required fields', 'error');
      return;
    }
    setSaving(true);
    try {
      await voiceGreetingsApi.create(formData);
      setDialogOpen(false);
      setFormData({ name: '', greeting_type: 'welcome', text: '', language: 'en' });
      fetchData();
      showSnackbar('Greeting created successfully', 'success');
    } catch (error) { 
      showSnackbar('Failed to create greeting', 'error');
    }
    finally { setSaving(false); }
  };

  const handleEdit = async () => {
    if (!selectedType || !editData.text) return;
    setSaving(true);
    try {
      await voiceGreetingsApi.update(selectedType, { text: editData.text });
      setEditDialogOpen(false);
      setSelectedType(null);
      fetchData();
      showSnackbar('Greeting updated successfully', 'success');
    } catch (error) {
      showSnackbar('Failed to update greeting', 'error');
    }
    finally { setSaving(false); }
  };

  const handleActivate = async (greetingType: string) => {
    try {
      await voiceGreetingsApi.update(greetingType, { is_active: true });
      fetchData();
      showSnackbar('Greeting activated', 'success');
    } catch (error) { 
      showSnackbar('Failed to activate greeting', 'error');
    }
  };

  const handleDelete = async () => {
    if (!selectedType) return;
    setSaving(true);
    try {
      await voiceGreetingsApi.delete(selectedType);
      setDeleteDialogOpen(false);
      setSelectedType(null);
      fetchData();
      showSnackbar('Greeting deleted', 'success');
    } catch (error) {
      showSnackbar('Failed to delete greeting', 'error');
    }
    finally { setSaving(false); }
  };

  const openEditDialog = (type: string, currentText: string) => {
    setSelectedType(type);
    setEditData({ text: currentText });
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (type: string) => {
    setSelectedType(type);
    setDeleteDialogOpen(true);
  };

  const openCreateDialog = (type: string) => {
    setFormData({ 
      name: GREETING_TYPE_INFO[type]?.label || type, 
      greeting_type: type, 
      text: '', 
      language: 'en' 
    });
    setDialogOpen(true);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <VoiceIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4">Voice Greetings</Typography>
            <Typography variant="body2" color="text.secondary">
              Customize voice greetings for different call scenarios
            </Typography>
          </Box>
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {types.map((type) => {
            const greeting = greetings.find((g) => g.type === type);
            const typeInfo = GREETING_TYPE_INFO[type] || { label: type, description: '' };
            
            return (
              <Grid item xs={12} md={6} key={type}>
                <Card 
                  sx={{ 
                    height: '100%',
                    border: greeting?.is_active ? '2px solid' : '1px solid',
                    borderColor: greeting?.is_active ? 'success.main' : 'divider',
                    opacity: greeting?.is_active ? 1 : 0.9,
                    transition: 'all 0.2s',
                    '&:hover': { boxShadow: 3 }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6">{typeInfo.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {typeInfo.description}
                        </Typography>
                      </Box>
                      {greeting?.is_active && (
                        <Chip 
                          icon={<CheckIcon />} 
                          label="Active" 
                          color="success" 
                          size="small" 
                          variant="outlined"
                        />
                      )}
                    </Box>
                    
                    <Divider sx={{ mb: 2 }} />
                    
                    {greeting ? (
                      <>
                        <Paper 
                          variant="outlined" 
                          sx={{ 
                            p: 2, 
                            mb: 2, 
                            bgcolor: 'grey.50',
                            minHeight: 60
                          }}
                        >
                          <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                            "{greeting.text}"
                          </Typography>
                        </Paper>
                        
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {!greeting.is_active && (
                            <Button 
                              size="small" 
                              variant="contained"
                              onClick={() => handleActivate(type)}
                            >
                              Activate
                            </Button>
                          )}
                          <Button 
                            size="small" 
                            variant="outlined"
                            startIcon={<EditIcon />}
                            onClick={() => openEditDialog(type, greeting.text)}
                          >
                            Edit
                          </Button>
                          <Button 
                            size="small" 
                            color="error"
                            startIcon={<DeleteIcon />}
                            onClick={() => openDeleteDialog(type)}
                          >
                            Delete
                          </Button>
                        </Box>
                      </>
                    ) : (
                      <>
                        <Alert severity="info" sx={{ mb: 2 }}>
                          No custom greeting configured. The system will use a default greeting.
                        </Alert>
                        <Button 
                          variant="outlined" 
                          startIcon={<AddIcon />}
                          onClick={() => openCreateDialog(type)}
                        >
                          Create Greeting
                        </Button>
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Create "{GREETING_TYPE_INFO[formData.greeting_type]?.label || formData.greeting_type}" Greeting
        </DialogTitle>
        <DialogContent>
          <TextField 
            fullWidth 
            label="Greeting Name" 
            value={formData.name} 
            onChange={(e) => setFormData({ ...formData, name: e.target.value })} 
            sx={{ mt: 2, mb: 2 }} 
            placeholder="e.g., Main Welcome Message"
          />
          <TextField 
            fullWidth 
            multiline 
            rows={4} 
            label="Greeting Text" 
            value={formData.text} 
            onChange={(e) => setFormData({ ...formData, text: e.target.value })} 
            placeholder="Thank you for calling [Business Name]. How may I help you today?"
            helperText="Use [Business Name] as a placeholder for your business name"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={saving}>
            {saving ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Greeting</DialogTitle>
        <DialogContent>
          <TextField 
            fullWidth 
            multiline 
            rows={4} 
            label="Greeting Text" 
            value={editData.text} 
            onChange={(e) => setEditData({ text: e.target.value })} 
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleEdit} disabled={saving}>
            {saving ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Greeting?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this greeting? The system will use a default greeting instead.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={handleDelete} disabled={saving}>
            {saving ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={4000} 
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
