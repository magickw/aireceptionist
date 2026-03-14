'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress, 
  Grid, Chip, IconButton, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Alert, Tabs, Tab, Paper, List, ListItem, ListItemText, Divider, Tooltip
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SchoolIcon from '@mui/icons-material/School';
import QuizIcon from '@mui/icons-material/Quiz';
import HistoryIcon from '@mui/icons-material/History';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AssessmentIcon from '@mui/icons-material/Assessment';
import RestoreIcon from '@mui/icons-material/Restore';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';

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
  const { isAuthenticated } = useAuth();
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [scenarios, setScenarios] = useState<TrainingScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [generateCount, setGenerateCount] = useState(5);
  const [editingScenario, setEditingScenario] = useState<TrainingScenario | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [isSnapshotLoading, setIsSnapshotLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [rollbackLoading, setRollbackLoading] = useState<number | null>(null);

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
    if (isAuthenticated) {
      fetchBusinessAndData();
    }
  }, [isAuthenticated]);

  const fetchBusinessAndData = async () => {
    try {
      const businessResponse = await api.get('/businesses');
      if (businessResponse.data.length > 0) {
        const bizId = businessResponse.data[0].id;
        setBusinessId(bizId);
        // Now fetch training data with the business ID
        await fetchScenarios(bizId);
        await fetchStats(bizId);
        await fetchSnapshots();
        await fetchBenchmarks(bizId);
      }
    } catch (error) {
      console.error('Failed to fetch business data', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScenarios = async (bizId?: number) => {
    const id = bizId || businessId;
    if (!id) return;
    try {
      const res = await api.get('/ai-training/', { params: { business_id: id } });
      setScenarios(res.data);
    } catch (error) {
      console.error('Failed to fetch scenarios', error);
    }
  };

  const fetchStats = async (bizId?: number) => {
    const id = bizId || businessId;
    if (!id) return;
    try {
      const res = await api.get('/ai-training/stats', { params: { business_id: id } });
      setStats(res.data);
    } catch (error) {
      console.error('Failed to fetch stats', error);
    }
  };

  const fetchSnapshots = async () => {
    try {
      const res = await api.get('/ai-training/snapshots');
      setSnapshots(res.data);
    } catch (error) {
      console.error('Failed to fetch snapshots', error);
    }
  };

  const fetchBenchmarks = async (bizId?: number) => {
    const id = bizId || businessId;
    if (!id) return;
    try {
      const res = await api.get('/ai-training/benchmarks', { params: { business_id: id } });
      setBenchmarks(res.data);
    } catch (error) {
      console.error('Failed to fetch benchmarks', error);
    }
  };

  const handleCreateSnapshot = async () => {
    if (!businessId) return;
    const name = prompt('Enter a name for this snapshot:');
    if (!name) return;
    setIsSnapshotLoading(true);
    try {
      await api.post(`/ai-training/snapshots?name=${encodeURIComponent(name)}&business_id=${businessId}`);
      fetchSnapshots();
      alert('Snapshot created successfully!');
    } catch (error) {
      console.error('Failed to create snapshot', error);
    } finally {
      setIsSnapshotLoading(false);
    }
  };

  const handleRollbackSnapshot = async (snapshotId: number) => {
    if (!businessId || !confirm('Are you sure you want to rollback to this snapshot? Current training data will be replaced.')) return;
    setRollbackLoading(snapshotId);
    try {
      await api.post(`/ai-training/snapshots/${snapshotId}/rollback?business_id=${businessId}`);
      await fetchScenarios();
      alert('Rollback completed successfully!');
    } catch (error) {
      console.error('Failed to rollback snapshot', error);
      alert('Failed to rollback snapshot');
    } finally {
      setRollbackLoading(null);
    }
  };

  const handleRunBenchmark = async () => {
    if (!businessId) return;
    setBenchmarkLoading(true);
    try {
      await api.post('/ai-training/test-all', null, { params: { business_id: businessId } });
      fetchBenchmarks();
      fetchStats();
      alert('Benchmark run complete!');
    } catch (error) {
      console.error('Failed to run benchmark', error);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.post('/ai-training/generate', null, { params: { count: generateCount } });
      setGenerateDialogOpen(false);
      fetchScenarios();
      fetchStats();
      alert('Successfully generated synthetic scenarios!');
    } catch (error) {
      console.error('Failed to generate scenarios', error);
      alert('Failed to generate scenarios. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!businessId) return;
    setSaving(true);
    try {
      if (editingScenario?.id) {
        await api.put(`/ai-training/${editingScenario.id}`, { ...formData, business_id: businessId });
      } else {
        await api.post('/ai-training', { ...formData, business_id: businessId });
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
    if (!businessId || !confirm('Delete this training scenario?')) return;
    try {
      await api.delete(`/ai-training/${id}`, { params: { business_id: businessId } });
      fetchScenarios();
      fetchStats();
    } catch (error) {
      console.error('Failed to delete scenario', error);
    }
  };

  const handleTest = async () => {
    if (!businessId || !testInput.trim()) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post('/ai-training/test-input', { 
        input: testInput,
        business_id: businessId 
      });
      setTestResult(res.data);
    } catch (error: any) {
      alert(`Error: ${error.message}`);
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

  if (!businessId) return (
    <Container sx={{ p: 4 }}>
      <Alert severity="warning">Please log in and select a business to access AI Training.</Alert>
    </Container>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <SchoolIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          AI Training
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<HistoryIcon />} 
            onClick={handleCreateSnapshot}
            sx={{ mr: 2 }}
            disabled={isSnapshotLoading}
          >
            {isSnapshotLoading ? 'Creating...' : 'Snapshot Brain'}
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<QuizIcon />} 
            onClick={() => setGenerateDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Generate Scenarios
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddNew}>
            Add Training Scenario
          </Button>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Train your AI receptionist with custom scenarios. Add Q&A pairs and test how the AI responds to different customer queries.
      </Alert>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Training Scenarios" />
          <Tab label="AI Playground" />
          <Tab label="Benchmarking" />
          <Tab label="Snapshots" />
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
                        {scenario.description && (
                          <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 1 }}>
                            {scenario.description}
                          </Typography>
                        )}
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
        <Grid container spacing={3}>
          <Grid item xs={12} md={5}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <QuizIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Playground Input
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Enter a customer message to see the full reasoning details.
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  placeholder="e.g., I'd like to book an appointment for tomorrow at 2pm"
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <Button 
                  variant="contained" 
                  fullWidth
                  startIcon={<PlayArrowIcon />} 
                  onClick={handleTest}
                  disabled={testing || !testInput.trim()}
                >
                  {testing ? 'Processing...' : 'Run Reasoner'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={7}>
            {testResult ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Card sx={{ bgcolor: '#f0f9ff', border: '1px solid #bae6fd' }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="primary">Suggested Response:</Typography>
                    <Typography variant="h6" sx={{ mt: 1 }}>"{testResult.suggested_response}"</Typography>
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Chip label={`Intent: ${testResult.intent}`} size="small" color="primary" variant="outlined" />
                      <Chip label={`Confidence: ${Math.round(testResult.confidence * 100)}%`} size="small" variant="outlined" />
                      <Chip label={`Sentiment: ${testResult.sentiment}`} size="small" variant="outlined" />
                    </Box>
                  </CardContent>
                </Card>

                <Tabs value={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
                  <Tab label="Context & Thoughts" />
                </Tabs>

                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="overline" color="text.secondary">Knowledge Base Matches</Typography>
                  <Typography variant="body2" sx={{ mb: 2, mt: 0.5, bgcolor: '#f8fafc', p: 1, borderRadius: 1 }}>
                    {testResult.playground_context?.knowledge_base || "No relevant KB entries found."}
                  </Typography>

                  <Typography variant="overline" color="text.secondary">Few-Shot Training Examples</Typography>
                  <Typography variant="body2" sx={{ mt: 0.5, bgcolor: '#f8fafc', p: 1, borderRadius: 1, whiteSpace: 'pre-wrap' }}>
                    {testResult.playground_context?.training_examples || "No training scenarios matched."}
                  </Typography>
                </Paper>
              </Box>
            ) : (
              <Paper sx={{ p: 8, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: 'text.secondary' }}>
                <PsychologyIcon sx={{ fontSize: 64, mb: 2, mx: 'auto', opacity: 0.2 }} />
                <Typography>Run the reasoner to see how the AI processes the input</Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}

      {tabValue === 2 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Benchmark Runs</Typography>
            <Button 
              variant="contained" 
              color="secondary" 
              onClick={handleRunBenchmark}
              disabled={benchmarkLoading}
            >
              {benchmarkLoading ? 'Running Suite...' : 'Run All Scenarios'}
            </Button>
          </Box>

          <Grid container spacing={3}>
            {benchmarks.map((run) => (
              <Grid item xs={12} key={run.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Box>
                        <Typography variant="h6">Run #{run.id}</Typography>
                        <Typography variant="caption" color="text.secondary">{new Date(run.created_at).toLocaleString()}</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="h4" color={run.avg_score >= 80 ? 'success.main' : 'warning.main'}>
                          {Math.round(run.avg_score)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">Average Quality</Typography>
                      </Box>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Number(run.avg_score)} 
                      color={run.avg_score >= 80 ? 'success' : 'warning'}
                      sx={{ height: 8, borderRadius: 5, mb: 2 }}
                    />
                    <Typography variant="body2">
                      Passed: <strong>{run.passed_scenarios}</strong> / {run.total_scenarios}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            {benchmarks.length === 0 && (
              <Grid item xs={12}>
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Typography color="text.secondary">No benchmark runs recorded yet.</Typography>
                </Paper>
              </Grid>
            )}
          </Grid>
        </Box>
      )}

      {tabValue === 3 && (
        <Box>
          <Typography variant="h6" gutterBottom>Version History (Snapshots)</Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {snapshots.map((snap) => (
              <Grid item xs={12} md={6} key={snap.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="h6">{snap.name}</Typography>
                      <Chip label={`v${snap.version}`} size="small" color="primary" />
                    </Box>
                    <Typography variant="body2" sx={{ my: 1 }}>{snap.description || 'No description'}</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        {snap.scenario_count} scenarios • Created {new Date(snap.created_at).toLocaleDateString()}
                      </Typography>
                      <Typography variant="subtitle2" color="success.main">
                        Score: {Math.round(snap.avg_success_rate)}%
                      </Typography>
                    </Box>
                    <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={rollbackLoading === snap.id ? <LinearProgress sx={{ width: 16 }} /> : <RestoreIcon />}
                        onClick={() => handleRollbackSnapshot(snap.id)}
                        disabled={rollbackLoading !== null}
                        color="warning"
                      >
                        Rollback
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            {snapshots.length === 0 && (
              <Grid item xs={12}>
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Typography color="text.secondary">No snapshots saved yet.</Typography>
                </Paper>
              </Grid>
            )}
          </Grid>
        </Box>
      )}

      {tabValue === 4 && stats && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary">{stats.total_scenarios || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Total Scenarios</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="success.main">{stats.active_scenarios || 0}</Typography>
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
          
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Performance by Category</Typography>
            <Paper variant="outlined">
              <List>
                {Object.entries(stats.by_category || {}).map(([cat, data]: [string, any], index, arr) => (
                  <React.Fragment key={cat}>
                    <ListItem>
                      <ListItemText 
                        primary={cat.replace('_', ' ').toUpperCase()} 
                        secondary={`${data.count} scenarios`}
                      />
                      <Box sx={{ minWidth: 100, textAlign: 'right' }}>
                        <Typography variant="h6" color={data.avg_success >= 80 ? 'success.main' : 'warning.main'}>
                          {Math.round(data.avg_success)}%
                        </Typography>
                      </Box>
                    </ListItem>
                    {index < arr.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Generate Dialog */}
      <Dialog open={generateDialogOpen} onClose={() => setGenerateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Synthetic Scenarios</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3, mt: 1 }}>
            Automatically generate training scenarios based on your business profile (services, type, and menu).
            This helps jumpstart your AI's training.
          </Typography>
          
          <FormControl fullWidth>
            <InputLabel>Number of Scenarios</InputLabel>
            <Select
              value={generateCount}
              label="Number of Scenarios"
              onChange={(e) => setGenerateCount(Number(e.target.value))}
            >
              <MenuItem value={3}>3 Scenarios</MenuItem>
              <MenuItem value={5}>5 Scenarios</MenuItem>
              <MenuItem value={10}>10 Scenarios</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleGenerate} 
            variant="contained" 
            color="primary"
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit/Add Dialog */}
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
