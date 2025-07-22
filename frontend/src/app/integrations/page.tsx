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
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import FormControlLabel from '@mui/material/FormControlLabel';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AssessmentIcon from '@mui/icons-material/Assessment';
import CloudIcon from '@mui/icons-material/Cloud';
import StorageIcon from '@mui/icons-material/Storage';
import PhoneIcon from '@mui/icons-material/Phone';
import LanguageIcon from '@mui/icons-material/Language';
import PeopleIcon from '@mui/icons-material/People';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import SettingsIcon from '@mui/icons-material/Settings';
import ChatIcon from '@mui/icons-material/Chat';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'connected' | 'disconnected' | 'error';
  icon: React.ReactNode;
  features: string[];
  setupRequired: boolean;
  lastSync?: Date;
  config?: Record<string, any>;
}

export default function Integrations() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Mock integrations data
    const mockIntegrations: Integration[] = [
      {
        id: 'google-calendar',
        name: 'Google Calendar',
        description: 'Sync appointments with Google Calendar for seamless scheduling',
        category: 'Calendar',
        status: 'disconnected',
        icon: <CalendarTodayIcon />,
        features: ['Appointment sync', 'Availability checking', 'Meeting reminders'],
        setupRequired: true,
      },
      {
        id: 'microsoft-outlook',
        name: 'Microsoft Outlook',
        description: 'Connect with Outlook calendar and email system',
        category: 'Calendar',
        status: 'disconnected',
        icon: <CalendarTodayIcon />,
        features: ['Calendar integration', 'Email notifications', 'Contact sync'],
        setupRequired: true,
      },
      {
        id: 'square-pos',
        name: 'Square POS',
        description: 'Integrate with Square for payment processing and inventory',
        category: 'POS',
        status: 'disconnected',
        icon: <AssessmentIcon />,
        features: ['Payment processing', 'Inventory sync', 'Customer data'],
        setupRequired: true,
      },
      {
        id: 'shopify',
        name: 'Shopify',
        description: 'Connect with Shopify for e-commerce integration',
        category: 'E-commerce',
        status: 'disconnected',
        icon: <StorageIcon />,
        features: ['Product catalog', 'Order management', 'Customer sync'],
        setupRequired: true,
      },
      {
        id: 'salesforce',
        name: 'Salesforce CRM',
        description: 'Sync customer data and interactions with Salesforce',
        category: 'CRM',
        status: 'disconnected',
        icon: <PeopleIcon />,
        features: ['Contact management', 'Lead tracking', 'Activity logging'],
        setupRequired: true,
      },
      {
        id: 'hubspot',
        name: 'HubSpot',
        description: 'Connect with HubSpot for comprehensive CRM functionality',
        category: 'CRM',
        status: 'disconnected',
        icon: <PeopleIcon />,
        features: ['Contact sync', 'Deal tracking', 'Marketing automation'],
        setupRequired: true,
      },
      {
        id: 'twilio',
        name: 'Twilio',
        description: 'Enhanced phone system integration with Twilio',
        category: 'Communication',
        status: 'connected',
        icon: <PhoneIcon />,
        features: ['Voice calls', 'SMS messaging', 'Call recording'],
        setupRequired: false,
        lastSync: new Date(),
        config: { accountSid: 'ACxxxxx', phoneNumber: '+1234567890' },
      },
      {
        id: 'slack',
        name: 'Slack',
        description: 'Get notifications and updates in your Slack workspace',
        category: 'Communication',
        status: 'disconnected',
        icon: <ChatIcon />,
        features: ['Call notifications', 'Appointment alerts', 'Team updates'],
        setupRequired: true,
      },
      {
        id: 'zapier',
        name: 'Zapier',
        description: 'Connect with 3000+ apps through Zapier automation',
        category: 'Automation',
        status: 'disconnected',
        icon: <SmartToyIcon />,
        features: ['Custom workflows', 'Data synchronization', 'Automated actions'],
        setupRequired: true,
      },
      {
        id: 'google-analytics',
        name: 'Google Analytics',
        description: 'Track call performance and customer interactions',
        category: 'Analytics',
        status: 'disconnected',
        icon: <AssessmentIcon />,
        features: ['Call tracking', 'Conversion analytics', 'Performance reports'],
        setupRequired: true,
      },
    ];

    setIntegrations(mockIntegrations);
    setIsLoading(false);
  }, []);

  const handleToggleIntegration = (integrationId: string) => {
    setIntegrations(prev => prev.map(integration => {
      if (integration.id === integrationId) {
        if (integration.status === 'connected') {
          return { ...integration, status: 'disconnected' };
        } else if (integration.setupRequired) {
          setSelectedIntegration(integration);
          setConfigDialogOpen(true);
          return integration;
        } else {
          return { ...integration, status: 'connected', lastSync: new Date() };
        }
      }
      return integration;
    }));
  };

  const handleConfigSave = () => {
    if (selectedIntegration) {
      setIntegrations(prev => prev.map(integration => 
        integration.id === selectedIntegration.id 
          ? { ...integration, status: 'connected' as const, lastSync: new Date(), setupRequired: false }
          : integration
      ));
    }
    setConfigDialogOpen(false);
    setSelectedIntegration(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'success';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircleIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <SettingsIcon color="action" />;
    }
  };

  const categories = [...new Set(integrations.map(i => i.category))];

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Integrations
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Connect your AI receptionist with your favorite business tools
        </Typography>
      </Box>

      {/* Integration Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'success.main', mx: 'auto', mb: 1 }}>
                <CheckCircleIcon />
              </Avatar>
              <Typography variant="h6">
                {integrations.filter(i => i.status === 'connected').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Connected
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'info.main', mx: 'auto', mb: 1 }}>
                <CloudIcon />
              </Avatar>
              <Typography variant="h6">
                {integrations.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Available
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'warning.main', mx: 'auto', mb: 1 }}>
                <SettingsIcon />
              </Avatar>
              <Typography variant="h6">
                {integrations.filter(i => i.setupRequired).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Setup Required
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'error.main', mx: 'auto', mb: 1 }}>
                <ErrorIcon />
              </Avatar>
              <Typography variant="h6">
                {integrations.filter(i => i.status === 'error').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Errors
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Integration Categories */}
      {categories.map((category) => (
        <Card key={category} sx={{ mb: 3 }}>
          <CardHeader
            title={category}
            subheader={`${integrations.filter(i => i.category === category).length} integrations available`}
          />
          <CardContent>
            <Grid container spacing={2}>
              {integrations
                .filter(integration => integration.category === category)
                .map((integration) => (
                  <Grid item xs={12} md={6} lg={4} key={integration.id}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                            {integration.icon}
                          </Avatar>
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="h6">{integration.name}</Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {getStatusIcon(integration.status)}
                              <Chip
                                label={integration.status.toUpperCase()}
                                color={getStatusColor(integration.status) as any}
                                size="small"
                              />
                            </Box>
                          </Box>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {integration.description}
                        </Typography>
                        
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Features:</Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {integration.features.slice(0, 3).map((feature, index) => (
                              <Chip key={index} label={feature} size="small" variant="outlined" />
                            ))}
                          </Box>
                        </Box>

                        {integration.status === 'connected' && integration.lastSync && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                            Last synced: {integration.lastSync.toLocaleString()}
                          </Typography>
                        )}

                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={integration.status === 'connected'}
                                onChange={() => handleToggleIntegration(integration.id)}
                                color="primary"
                              />
                            }
                            label={integration.status === 'connected' ? 'Connected' : 'Connect'}
                          />
                          {integration.status === 'connected' && (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => {
                                setSelectedIntegration(integration);
                                setConfigDialogOpen(true);
                              }}
                            >
                              Configure
                            </Button>
                          )}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
            </Grid>
          </CardContent>
        </Card>
      ))}

      {/* Configuration Dialog */}
      <Dialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Configure {selectedIntegration?.name}
        </DialogTitle>
        <DialogContent>
          {selectedIntegration && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="info" sx={{ mb: 3 }}>
                To connect {selectedIntegration.name}, you'll need to provide your API credentials or authorize access.
              </Alert>
              
              {selectedIntegration.id === 'google-calendar' && (
                <Box>
                  <Typography variant="h6" gutterBottom>Google Calendar Setup</Typography>
                  <TextField
                    fullWidth
                    label="Google Client ID"
                    variant="outlined"
                    margin="normal"
                    helperText="Get this from your Google Cloud Console"
                  />
                  <TextField
                    fullWidth
                    label="Google Client Secret"
                    variant="outlined"
                    margin="normal"
                    type="password"
                  />
                  <Button variant="outlined" sx={{ mt: 2 }}>
                    Authorize with Google
                  </Button>
                </Box>
              )}

              {selectedIntegration.id === 'salesforce' && (
                <Box>
                  <Typography variant="h6" gutterBottom>Salesforce CRM Setup</Typography>
                  <TextField
                    fullWidth
                    label="Salesforce Instance URL"
                    variant="outlined"
                    margin="normal"
                    placeholder="https://your-instance.salesforce.com"
                  />
                  <TextField
                    fullWidth
                    label="API Username"
                    variant="outlined"
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="API Token"
                    variant="outlined"
                    margin="normal"
                    type="password"
                  />
                </Box>
              )}

              {selectedIntegration.id === 'square-pos' && (
                <Box>
                  <Typography variant="h6" gutterBottom>Square POS Setup</Typography>
                  <TextField
                    fullWidth
                    label="Square Application ID"
                    variant="outlined"
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="Square Access Token"
                    variant="outlined"
                    margin="normal"
                    type="password"
                  />
                  <TextField
                    fullWidth
                    label="Location ID"
                    variant="outlined"
                    margin="normal"
                    helperText="Square location to sync with"
                  />
                </Box>
              )}

              {!['google-calendar', 'salesforce', 'square-pos'].includes(selectedIntegration.id) && (
                <Box>
                  <Typography variant="h6" gutterBottom>{selectedIntegration.name} Setup</Typography>
                  <TextField
                    fullWidth
                    label="API Key"
                    variant="outlined"
                    margin="normal"
                    type="password"
                  />
                  <TextField
                    fullWidth
                    label="API Secret (if required)"
                    variant="outlined"
                    margin="normal"
                    type="password"
                  />
                  <TextField
                    fullWidth
                    label="Webhook URL"
                    variant="outlined"
                    margin="normal"
                    value="https://your-app.com/webhooks"
                    disabled
                    helperText="Use this URL in your integration settings"
                  />
                </Box>
              )}

              <Divider sx={{ my: 3 }} />
              
              <Typography variant="h6" gutterBottom>Features Enabled</Typography>
              <List>
                {selectedIntegration.features.map((feature, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={feature} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleConfigSave}>
            {selectedIntegration?.status === 'connected' ? 'Save Changes' : 'Connect'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}