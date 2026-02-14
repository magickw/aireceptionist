'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import IconButton from '@mui/material/IconButton';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Paper from '@mui/material/Paper';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PsychologyIcon from '@mui/icons-material/Psychology';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ChatIcon from '@mui/icons-material/Chat';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import axios from 'axios';

interface TrainingScenario {
  id: number;
  title: string;
  description: string;
  user_input: string;
  expected_response: string;
  category: string;
  is_active: boolean;
  success_rate?: number;
  last_tested?: string;
  created_at: string;
  updated_at: string;
}

interface AITestResponse {
  response: string;
  confidence: number;
  intent: string;
  entities: any;
}

interface ScenarioAnalytics {
  categoryStats: Array<{
    category: string;
    total_scenarios: number;
    active_scenarios: number;
    avg_success_rate: number;
    tested_scenarios: number;
  }>;
  recentTests: Array<{
    created_at: string;
    scenario_id: string;
    user_input: string;
  }>;
  totalScenarios: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export default function AITraining() {
  const [tabValue, setTabValue] = useState(0);
  const [scenarios, setScenarios] = useState<TrainingScenario[]>([]);
  const [analytics, setAnalytics] = useState<ScenarioAnalytics | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState<TrainingScenario | null>(null);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [testLoading, setTestLoading] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testResponse, setTestResponse] = useState<AITestResponse | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  
  const [newScenario, setNewScenario] = useState<Omit<TrainingScenario, 'id' | 'created_at' | 'updated_at'>>({
    title: '',
    description: '',
    user_input: '',
    expected_response: '',
    category: '',
    is_active: true,
  });

  const [aiPersonality, setAiPersonality] = useState({
    tone: 'professional',
    greeting: 'Hello! Thank you for calling. How can I help you today?',
    transferMessage: 'Let me transfer you to the right person who can help you better.',
    unavailableMessage: 'I apologize, but we are currently closed. Our business hours are...',
    holdMessage: 'Please hold while I check that information for you.',
  });

  useEffect(() => {
    const fetchBusinessId = async () => {
      try {
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/businesses`);
        if (businessResponse.data.length > 0) {
          setBusinessId(businessResponse.data[0].id);
        }
      } catch (error) {
        console.error('Error fetching business ID:', error);
      }
    };
    fetchBusinessId();
  }, []);

  useEffect(() => {
    if (!businessId) return;
    fetchData();
  }, [businessId]);

  const fetchData = async () => {
    if (!businessId) return;
    
    try {
      setLoading(true);
      const [scenariosResponse, analyticsResponse] = await Promise.all([
        axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/scenarios`),
        axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/scenarios/analytics`)
      ]);
      
      setScenarios(scenariosResponse.data);
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      setSnackbar({ open: true, message: 'Error loading training data', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAddScenario = () => {
    setEditingScenario(null);
    setNewScenario({
      title: '',
      description: '',
      user_input: '',
      expected_response: '',
      category: '',
      is_active: true,
    });
    setDialogOpen(true);
  };

  const handleEditScenario = (scenario: TrainingScenario) => {
    setEditingScenario(scenario);
    setNewScenario({
      title: scenario.title,
      description: scenario.description,
      user_input: scenario.user_input,
      expected_response: scenario.expected_response,
      category: scenario.category,
      is_active: scenario.is_active,
    });
    setDialogOpen(true);
  };

  const handleSaveScenario = async () => {
    if (!businessId) return;
    
    try {
      if (editingScenario) {
        await axios.put(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/scenarios/${editingScenario.id}`,
          newScenario
        );
        setSnackbar({ open: true, message: 'Scenario updated successfully', severity: 'success' });
      } else {
        await axios.post(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/scenarios`,
          newScenario
        );
        setSnackbar({ open: true, message: 'Scenario created successfully', severity: 'success' });
      }
      
      setDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error saving scenario:', error);
      setSnackbar({ open: true, message: 'Error saving scenario', severity: 'error' });
    }
  };

  const handleDeleteScenario = async (id: number) => {
    if (!businessId) return;
    
    try {
      await axios.delete(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/scenarios/${id}`);
      setSnackbar({ open: true, message: 'Scenario deleted successfully', severity: 'success' });
      fetchData();
    } catch (error) {
      console.error('Error deleting scenario:', error);
      setSnackbar({ open: true, message: 'Error deleting scenario', severity: 'error' });
    }
  };

  const handleToggleScenario = async (scenario: TrainingScenario) => {
    if (!businessId) return;
    
    try {
      await axios.put(
        `${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/scenarios/${scenario.id}`,
        { ...scenario, is_active: !scenario.is_active }
      );
      fetchData();
    } catch (error) {
      console.error('Error toggling scenario:', error);
      setSnackbar({ open: true, message: 'Error updating scenario', severity: 'error' });
    }
  };

  const handleTestResponse = async (scenarioId?: number) => {
    if (!businessId || !testInput) return;
    
    try {
      setTestLoading(true);
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/ai-training/business/${businessId}/test-response`,
        {
          user_input: testInput,
          scenario_id: scenarioId
        }
      );
      
      setTestResponse(response.data);
      if (scenarioId) {
        fetchData(); // Refresh to update last_tested timestamp
      }
    } catch (error) {
      console.error('Error testing response:', error);
      setSnackbar({ open: true, message: 'Error testing AI response', severity: 'error' });
    } finally {
      setTestLoading(false);
    }
  };

  const handlePersonalityChange = (field: string, value: string) => {
    setAiPersonality({ ...aiPersonality, [field]: value });
  };

  const categories = [...new Set(scenarios.map(s => s.category))].filter(Boolean);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          AI Training Center
        </Typography>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          AI Training Center
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Train your AI receptionist with custom scenarios and monitor performance
        </Typography>
      </Box>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Training Scenarios" />
        <Tab label="AI Testing" />
        <Tab label="Analytics" />
        <Tab label="AI Personality" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* Training Scenarios */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardHeader
                avatar={
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <PsychologyIcon />
                  </Avatar>
                }
                title="Training Scenarios"
                subheader={`${scenarios.length} scenarios • ${scenarios.filter(s => s.is_active).length} active`}
                action={
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      startIcon={<UploadFileIcon />}
                      size="small"
                    >
                      Import
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleAddScenario}
                    >
                      Add Scenario
                    </Button>
                  </Box>
                }
              />
              <CardContent>
                {categories.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="textSecondary">
                      No training scenarios found. Create your first scenario to get started.
                    </Typography>
                  </Box>
                ) : (
                  categories.map((category) => (
                    <Accordion key={category} sx={{ mb: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="h6">{category}</Typography>
                          <Chip
                            label={`${scenarios.filter(s => s.category === category && s.is_active).length} active`}
                            size="small"
                            color="primary"
                          />
                          <Chip
                            label={`${scenarios.filter(s => s.category === category).length} total`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List>
                          {scenarios
                            .filter(s => s.category === category)
                            .map((scenario) => (
                              <ListItem key={scenario.id} divider>
                                <ListItemText
                                  primary={
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                      <Typography variant="subtitle1">{scenario.title}</Typography>
                                      <FormControlLabel
                                        control={
                                          <Switch
                                            checked={scenario.is_active}
                                            onChange={() => handleToggleScenario(scenario)}
                                            size="small"
                                          />
                                        }
                                        label="Active"
                                      />
                                      {scenario.last_tested && (
                                        <Chip
                                          label={`Tested ${new Date(scenario.last_tested).toLocaleDateString()}`}
                                          size="small"
                                          color="success"
                                        />
                                      )}
                                    </Box>
                                  }
                                  secondary={
                                    <Box>
                                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                                        {scenario.description}
                                      </Typography>
                                      <Typography variant="caption" color="primary">
                                        Input: {scenario.user_input.substring(0, 100)}...
                                      </Typography>
                                      <br />
                                      <Typography variant="caption" color="success.main">
                                        Response: {scenario.expected_response.substring(0, 100)}...
                                      </Typography>
                                    </Box>
                                  }
                                />
                                <ListItemSecondaryAction>
                                  <IconButton
                                    edge="end"
                                    onClick={() => {
                                      setTestInput(scenario.user_input);
                                      setTestDialogOpen(true);
                                    }}
                                    sx={{ mr: 1 }}
                                    title="Test scenario"
                                  >
                                    <PlayArrowIcon />
                                  </IconButton>
                                  <IconButton
                                    edge="end"
                                    onClick={() => handleEditScenario(scenario)}
                                    sx={{ mr: 1 }}
                                  >
                                    <EditIcon />
                                  </IconButton>
                                  <IconButton
                                    edge="end"
                                    onClick={() => handleDeleteScenario(scenario.id)}
                                  >
                                    <DeleteIcon />
                                  </IconButton>
                                </ListItemSecondaryAction>
                              </ListItem>
                            ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  ))
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* AI Testing */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'success.main' }}><ChatIcon /></Avatar>}
                title="Test AI Responses"
                subheader="Test how your AI responds to different inputs"
              />
              <CardContent>
                <TextField
                  label="Test Input"
                  variant="outlined"
                  fullWidth
                  multiline
                  rows={3}
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  placeholder="Enter what a customer might say..."
                  sx={{ mb: 2 }}
                />
                <Button
                  variant="contained"
                  onClick={() => handleTestResponse()}
                  disabled={!testInput || testLoading}
                  fullWidth
                  startIcon={testLoading ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                >
                  {testLoading ? 'Testing...' : 'Test AI Response'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                title="AI Response"
                subheader="How your AI will respond"
              />
              <CardContent>
                {testResponse ? (
                  <Box>
                    <Paper sx={{ p: 2, mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                      <Typography variant="body1">
                        {testResponse.response}
                      </Typography>
                    </Paper>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Chip
                        label={`Confidence: ${Math.round(testResponse.confidence * 100)}%`}
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={`Intent: ${testResponse.intent}`}
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                    {testResponse.entities && Object.keys(testResponse.entities).length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Extracted Entities:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {Object.entries(testResponse.entities).map(([key, value]) => (
                            <Chip
                              key={key}
                              label={`${key}: ${value}`}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Typography color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
                    Enter a test input and click "Test AI Response" to see how your AI will respond
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Analytics */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'info.main' }}><AnalyticsIcon /></Avatar>}
                title="Training Analytics"
                subheader="Performance metrics for your training scenarios"
              />
              <CardContent>
                {analytics ? (
                  <Grid container spacing={3}>
                    {analytics.categoryStats.map((stat) => (
                      <Grid item xs={12} sm={6} key={stat.category}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            {stat.category}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2">Total Scenarios:</Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {stat.total_scenarios}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2">Active:</Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {stat.active_scenarios}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2">Tested:</Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {stat.tested_scenarios}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                            <Typography variant="body2">Success Rate:</Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {Math.round(stat.avg_success_rate || 0)}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={stat.avg_success_rate || 0}
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Typography color="textSecondary">No analytics data available</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader
                title="Recent Tests"
                subheader="Latest scenario testing activity"
              />
              <CardContent>
                {analytics?.recentTests.length ? (
                  <List>
                    {analytics.recentTests.map((test, index) => (
                      <ListItem key={index} divider>
                        <ListItemText
                          primary={test.user_input.substring(0, 50) + '...'}
                          secondary={new Date(test.created_at).toLocaleString()}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="textSecondary">No recent tests</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* AI Personality */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                avatar={
                  <Avatar sx={{ bgcolor: 'success.main' }}>
                    <SmartToyIcon />
                  </Avatar>
                }
                title="AI Personality Settings"
                subheader="Define your AI's tone and communication style"
              />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <TextField
                      label="Greeting Message"
                      variant="outlined"
                      fullWidth
                      multiline
                      rows={2}
                      value={aiPersonality.greeting}
                      onChange={(e) => handlePersonalityChange('greeting', e.target.value)}
                      helperText="First message customers hear when calling"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Transfer Message"
                      variant="outlined"
                      fullWidth
                      multiline
                      rows={2}
                      value={aiPersonality.transferMessage}
                      onChange={(e) => handlePersonalityChange('transferMessage', e.target.value)}
                      helperText="Message when transferring to human agent"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="After Hours Message"
                      variant="outlined"
                      fullWidth
                      multiline
                      rows={2}
                      value={aiPersonality.unavailableMessage}
                      onChange={(e) => handlePersonalityChange('unavailableMessage', e.target.value)}
                      helperText="Message when business is closed"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Hold Message"
                      variant="outlined"
                      fullWidth
                      multiline
                      rows={2}
                      value={aiPersonality.holdMessage}
                      onChange={(e) => handlePersonalityChange('holdMessage', e.target.value)}
                      helperText="Message when putting customer on hold"
                    />
                  </Grid>
                </Grid>
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button variant="contained" color="primary">
                    Save Personality Settings
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                title="AI Behavior Preview"
                subheader="Test how your AI will respond"
              />
              <CardContent>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                  <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                    "Hello, I'd like to book an appointment for tomorrow."
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                  <Typography variant="body2">
                    {aiPersonality.greeting} I'd be happy to help you schedule an appointment. What service would you like to book and what time works best for you?
                  </Typography>
                </Paper>
                <Box sx={{ mt: 2 }}>
                  <Button 
                    variant="outlined" 
                    fullWidth
                    onClick={() => {
                      setTestInput("Hello, I'd like to book an appointment for tomorrow.");
                      setTestDialogOpen(true);
                    }}
                  >
                    Test AI Response
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Scenario Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingScenario ? 'Edit Training Scenario' : 'Add New Training Scenario'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Title"
                variant="outlined"
                fullWidth
                value={newScenario.title}
                onChange={(e) => setNewScenario({ ...newScenario, title: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Category"
                variant="outlined"
                fullWidth
                value={newScenario.category}
                onChange={(e) => setNewScenario({ ...newScenario, category: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                variant="outlined"
                fullWidth
                multiline
                rows={2}
                value={newScenario.description}
                onChange={(e) => setNewScenario({ ...newScenario, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Customer Input"
                variant="outlined"
                fullWidth
                multiline
                rows={3}
                value={newScenario.user_input}
                onChange={(e) => setNewScenario({ ...newScenario, user_input: e.target.value })}
                helperText="What the customer might say to trigger this response"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Expected AI Response"
                variant="outlined"
                fullWidth
                multiline
                rows={4}
                value={newScenario.expected_response}
                onChange={(e) => setNewScenario({ ...newScenario, expected_response: e.target.value })}
                helperText="How the AI should respond"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newScenario.is_active}
                    onChange={(e) => setNewScenario({ ...newScenario, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleSaveScenario}
            disabled={!newScenario.title || !newScenario.user_input || !newScenario.expected_response}
          >
            {editingScenario ? 'Update' : 'Add'} Scenario
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Dialog */}
      <Dialog
        open={testDialogOpen}
        onClose={() => setTestDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Test AI Response</DialogTitle>
        <DialogContent>
          <TextField
            label="Test Input"
            variant="outlined"
            fullWidth
            multiline
            rows={3}
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            sx={{ mt: 2 }}
          />
          {testResponse && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>AI Response:</Typography>
              <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                <Typography variant="body1">
                  {testResponse.response}
                </Typography>
              </Paper>
              <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`Confidence: ${Math.round(testResponse.confidence * 100)}%`} />
                <Chip label={`Intent: ${testResponse.intent}`} />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => handleTestResponse()}
            disabled={!testInput || testLoading}
            startIcon={testLoading ? <CircularProgress size={16} /> : <PlayArrowIcon />}
          >
            {testLoading ? 'Testing...' : 'Test Response'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}