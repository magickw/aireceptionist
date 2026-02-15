'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress, 
  Grid, Chip, IconButton, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Alert, Tabs, Tab, Paper, List, ListItem, ListItemText, Divider
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SchoolIcon from '@mui/icons-material/School';
import QuizIcon from '@mui/icons-material/Quiz';
import api from '@/services/api';

interface TrainingScenario {
  id?: number;
  title: string;
  user_input: string;
  expected_response: string;
  description: string;
  category: string;
  is_active: boolean;
}

const CATEGORIES = [
  'appointment_booking',
  'customer_support', 
  'sales_inquiry',
  'general_inquiry',
  'complaint_handling',
  'information_request',
  'ordering',
  'pricing',
  'hours_location'
];

export default function AITrainingPage() {
  const [scenarios, setScenarios] = useState<TrainingScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState<TrainingScenario | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState('');
  const [testing, setTesting] = useState(false);
  const [stats, setStats] = useState<any>(null);

  const emptyScenario: TrainingScenario = {
    title: '',
    user_input: '',
    expected_response: '',
    description: '',
    category: 'general_inquiry',
    is_active: true
  };

  const [formData, setFormData] = useState<TrainingScenario>(emptyScenario);

  useEffect(() => {
    fetchScenarios();
    fetchStats();
  }, []);

  const fetchScenarios = async () => {
    try {
      const res = await api.get('/ai-training/', { params: { business_id: 1 } });
      setScenarios(res.data);
    } catch (error) {
      console.error('Failed to fetch scenarios', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await api.get('/ai-training/statistics', { params: { business_id: 1 } });
      setStats(res.data);
    } catch (error) {
      console.error('Failed to fetch stats', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editingScenario?.id) {
        await api.put(`/ai-training/${editingScenario.id}`, { ...formData, business_id: 1 });
      } else {
        await api.post('/ai-training', { ...formData, business_id: 1 });
      }
      
      setDialogOpen(false);
      fetchScenarios();
      fetchStats();
      setFormData(emptyScenario);
      setEditingScenario(null);
    } catch (error) {
      console.error('Failed to save scenario', error);
      alert('Failed to save training scenario.');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (scenario: TrainingScenario) => {
    setEditingScenario(scenario);
    setFormData(scenario);
    setDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this training scenario?')) return;
    try {
      await api.delete(`/ai-training/${id}`, { params: { business_id: 1 } });
      fetchScenarios();
      fetchStats();
    } catch (error) {
      console.error('Failed to delete scenario', error);
    }
  };

  const handleTest = async () => {
    if (!testInput.trim()) return;
    setTesting(true);
    setTestResult('');
    try {
      const res = await api.post('/ai-training/test-input', { 
        input: testInput,
        business_id: 1 
      });
      setTestResult(JSON.stringify(res.data, null, 2));
    } catch (error: any) {
      setTestResult(`Error: ${error.message}`);
    } finally {
      setTesting(false);
    }
  };

  const handleAddNew = () => {
    setEditingScenario(null);
    setFormData(emptyScenario);
    setDialogOpen(true);
  };

  if (loading) return <Container sx={{ p: 4 }}><LinearProgress /></Container>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <SchoolIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          AI Training
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddNew}>
          Add Training Scenario
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Train your AI receptionist with custom scenarios. Add Q&A pairs and test how the AI responds to different customer queries.
      </Alert>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Training Scenarios" />
          <Tab label="Test AI" />
          <Tab label="Statistics" />
        </Tabs>
      </Box>

      {tabValue === 0 && (
        <>
          <Grid container spacing={2}>
            {scenarios.map((scenario) => (
              <Grid item xs={12} md={6} key={scenario.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h6">{scenario.title}</Typography>
                        <Chip label={scenario.category} size="small" sx={{ mb: 1 }} />
                        {!scenario.is_active && <Chip label="Inactive" size="small" color="error" />}
                      </Box>
                      <Box>
                        <IconButton size="small" onClick={() => handleEdit(scenario)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDelete(scenario.id!)}>
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="caption" color="text.secondary">Customer says:</Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                      "{scenario.user_input}"
                    </Typography>
                    <Typography variant="caption" color="text.secondary">AI should respond:</Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      "{scenario.expected_response}"
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          {scenarios.length === 0 && (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No training scenarios yet. Add your first scenario to train the AI!
              </Typography>
            </Paper>
          )}
        </>
      )}

      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <QuizIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Test AI Response
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Enter a customer message to see how the AI responds with current training.
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={3}
              placeholder="e.g., I'd like to book an appointment for tomorrow at 2pm"
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button 
              variant="contained" 
              startIcon={<PlayArrowIcon />} 
              onClick={handleTest}
              disabled={testing || !testInput.trim()}
            >
              {testing ? 'Testing...' : 'Test AI'}
            </Button>
            
            {testResult && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>AI Response:</Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '14px' }}>
                    {testResult}
                  </pre>
                </Paper>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {tabValue === 2 && stats && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary">{stats.total || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Total Scenarios</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="success.main">{stats.active || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Active</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="warning.main">{stats.by_category ? Object.keys(stats.by_category).length : 0}</Typography>
                <Typography variant="body2" color="text.secondary">Categories</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingScenario ? 'Edit Training Scenario' : 'Add Training Scenario'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Booking appointment for new patient"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  {CATEGORIES.map((cat) => (
                    <MenuItem key={cat} value={cat}>{cat.replace('_', ' ')}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Description (optional)"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Customer Input / Question"
                value={formData.user_input}
                onChange={(e) => setFormData({ ...formData, user_input: e.target.value })}
                placeholder="What the customer would say"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Expected AI Response"
                value={formData.expected_response}
                onChange={(e) => setFormData({ ...formData, expected_response: e.target.value })}
                placeholder="How the AI should respond"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={saving || !formData.title || !formData.user_input}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
