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
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PsychologyIcon from '@mui/icons-material/Psychology';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ChatIcon from '@mui/icons-material/Chat';

interface TrainingScenario {
  id: number;
  title: string;
  description: string;
  prompt: string;
  response: string;
  category: string;
  enabled: boolean;
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
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState<TrainingScenario | null>(null);
  const [newScenario, setNewScenario] = useState<TrainingScenario>({
    id: 0,
    title: '',
    description: '',
    prompt: '',
    response: '',
    category: '',
    enabled: true,
  });

  const [aiPersonality, setAiPersonality] = useState({
    tone: 'professional',
    greeting: 'Hello! Thank you for calling. How can I help you today?',
    transferMessage: 'Let me transfer you to the right person who can help you better.',
    unavailableMessage: 'I apologize, but we are currently closed. Our business hours are...',
    holdMessage: 'Please hold while I check that information for you.',
  });

  useEffect(() => {
    // Mock data for training scenarios
    setScenarios([
      {
        id: 1,
        title: 'Appointment Booking',
        description: 'Handle appointment booking requests',
        prompt: 'Customer wants to book an appointment',
        response: 'I\'d be happy to help you schedule an appointment. What service would you like to book and what day works best for you?',
        category: 'Booking',
        enabled: true,
      },
      {
        id: 2,
        title: 'Business Hours Inquiry',
        description: 'Provide business hours information',
        prompt: 'Customer asks about business hours',
        response: 'We are open Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 4 PM. We\'re closed on Sundays.',
        category: 'Information',
        enabled: true,
      },
      {
        id: 3,
        title: 'Service Information',
        description: 'Provide information about services offered',
        prompt: 'Customer asks about available services',
        response: 'We offer a wide range of services including consultations, treatments, and specialized procedures. Would you like me to provide details about any specific service?',
        category: 'Information',
        enabled: true,
      },
      {
        id: 4,
        title: 'Emergency Handling',
        description: 'Handle emergency situations',
        prompt: 'Customer has an emergency',
        response: 'I understand this is urgent. Let me immediately connect you with our emergency line or transfer you to someone who can help right away.',
        category: 'Emergency',
        enabled: true,
      },
    ]);
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAddScenario = () => {
    setEditingScenario(null);
    setNewScenario({
      id: 0,
      title: '',
      description: '',
      prompt: '',
      response: '',
      category: '',
      enabled: true,
    });
    setDialogOpen(true);
  };

  const handleEditScenario = (scenario: TrainingScenario) => {
    setEditingScenario(scenario);
    setNewScenario({ ...scenario });
    setDialogOpen(true);
  };

  const handleSaveScenario = () => {
    if (editingScenario) {
      setScenarios(scenarios.map(s => s.id === editingScenario.id ? { ...newScenario, id: editingScenario.id } : s));
    } else {
      setScenarios([...scenarios, { ...newScenario, id: Date.now() }]);
    }
    setDialogOpen(false);
  };

  const handleDeleteScenario = (id: number) => {
    setScenarios(scenarios.filter(s => s.id !== id));
  };

  const handleToggleScenario = (id: number) => {
    setScenarios(scenarios.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
  };

  const handlePersonalityChange = (field: string, value: string) => {
    setAiPersonality({ ...aiPersonality, [field]: value });
  };

  const categories = [...new Set(scenarios.map(s => s.category))];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          AI Training
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Customize your AI receptionist responses and train it for specific scenarios
        </Typography>
      </Box>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Training Scenarios" />
        <Tab label="AI Personality" />
        <Tab label="Response Templates" />
        <Tab label="Voice Settings" />
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
                subheader="Define how your AI should respond to different situations"
                action={
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleAddScenario}
                  >
                    Add Scenario
                  </Button>
                }
              />
              <CardContent>
                {categories.map((category) => (
                  <Accordion key={category} sx={{ mb: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="h6">{category}</Typography>
                        <Chip
                          label={`${scenarios.filter(s => s.category === category && s.enabled).length} active`}
                          size="small"
                          color="primary"
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
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Typography variant="subtitle1">{scenario.title}</Typography>
                                    <FormControlLabel
                                      control={
                                        <Switch
                                          checked={scenario.enabled}
                                          onChange={() => handleToggleScenario(scenario.id)}
                                          size="small"
                                        />
                                      }
                                      label="Enabled"
                                    />
                                  </Box>
                                }
                                secondary={`${scenario.description} • Sample Response: ${scenario.response.substring(0, 100)}...`}
                                secondaryTypographyProps={{ component: 'div' }}
                              />
                              <ListItemSecondaryAction>
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
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
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
                    &quot;Hello, I&apos;d like to book an appointment for tomorrow.&quot;
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                  <Typography variant="body2">
                    {aiPersonality.greeting} I&apos;d be happy to help you schedule an appointment. What service would you like to book and what time works best for you?
                  </Typography>
                </Paper>
                <Box sx={{ mt: 2 }}>
                  <Button variant="outlined" fullWidth>
                    Test AI Response
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Response Templates */}
        <Card>
          <CardHeader
            avatar={
              <Avatar sx={{ bgcolor: 'info.main' }}>
                <ChatIcon />
              </Avatar>
            }
            title="Response Templates"
            subheader="Pre-defined responses for common inquiries"
          />
          <CardContent>
            <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              Response templates will be available in the next update. This feature will allow you to create reusable response templates for common customer inquiries.
            </Typography>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* Voice Settings */}
        <Card>
          <CardHeader
            avatar={
              <Avatar sx={{ bgcolor: 'warning.main' }}>
                <RecordVoiceOverIcon />
              </Avatar>
            }
            title="Voice Settings"
            subheader="Configure AI voice characteristics"
          />
          <CardContent>
            <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              Voice settings will be available in the next update. This feature will allow you to customize the AI&apos;s voice, speaking speed, and accent.
            </Typography>
          </CardContent>
        </Card>
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
                label="Customer Prompt"
                variant="outlined"
                fullWidth
                multiline
                rows={3}
                value={newScenario.prompt}
                onChange={(e) => setNewScenario({ ...newScenario, prompt: e.target.value })}
                helperText="What the customer might say to trigger this response"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="AI Response"
                variant="outlined"
                fullWidth
                multiline
                rows={4}
                value={newScenario.response}
                onChange={(e) => setNewScenario({ ...newScenario, response: e.target.value })}
                helperText="How the AI should respond"
                required
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveScenario}>
            {editingScenario ? 'Update' : 'Add'} Scenario
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}