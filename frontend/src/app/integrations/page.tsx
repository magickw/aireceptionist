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
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Paper from '@mui/material/Paper';
import Snackbar from '@mui/material/Snackbar';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Badge from '@mui/material/Badge';
import Stack from '@mui/material/Stack';
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
import SyncIcon from '@mui/icons-material/Sync';
import RefreshIcon from '@mui/icons-material/Refresh';
import LaunchIcon from '@mui/icons-material/Launch';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import EmailIcon from '@mui/icons-material/Email';
import axios from 'axios';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'connected' | 'disconnected' | 'error' | 'connecting';
  icon: React.ReactNode;
  features: string[];
  authType: 'oauth2' | 'api_key' | 'webhook';
  lastSync?: string;
  config?: Record<string, any>;
  error_message?: string;
}

interface IntegrationType {
  type: string;
  name: string;
  description: string;
  integrations: Array<{
    id: string;
    name: string;
    description: string;
    features: string[];
    authType: string;
    icon: string;
    status: string;
  }>;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export default function Integrations() {
  const [tabValue, setTabValue] = useState(0);
  const [integrationTypes, setIntegrationTypes] = useState<IntegrationType[]>([]);
  const [userIntegrations, setUserIntegrations] = useState<Integration[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<any>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [oauthDialogOpen, setOAuthDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const [syncing, setSyncing] = useState<string | null>(null);

  const [configForm, setConfigForm] = useState<Record<string, any>>({});

  const getIntegrationIcon = (iconName: string) => {
    const icons: Record<string, React.ReactNode> = {
      'salesforce': <PeopleIcon />,
      'hubspot': <PeopleIcon />,
      'pipedrive': <PeopleIcon />,
      'google_calendar': <CalendarTodayIcon />,
      'microsoft': <CalendarTodayIcon />,
      'calendly': <CalendarTodayIcon />,
      'slack': <ChatIcon />,
      'teams': <ChatIcon />,
      'discord': <ChatIcon />,
      'stripe': <CreditCardIcon />,
      'square': <CreditCardIcon />,
      'paypal': <CreditCardIcon />,
      'google_analytics': <AssessmentIcon />,
      'mixpanel': <AssessmentIcon />,
      'shopify': <ShoppingCartIcon />,
      'woocommerce': <ShoppingCartIcon />,
    };
    return icons[iconName] || <LanguageIcon />;
  };

  useEffect(() => {
    const fetchBusinessId = async () => {
      try {
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
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
      setIsLoading(true);
      const [typesResponse, userIntegrationsResponse] = await Promise.all([
        axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/types`),
        axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/business/${businessId}`)
      ]);

      setIntegrationTypes(typesResponse.data);
      
      // Convert user integrations to the format expected by the UI
      const convertedIntegrations = userIntegrationsResponse.data.map((integration: any) => ({
        id: integration.integration_type,
        name: integration.name,
        description: 'Connected integration',
        category: getCategoryByType(integration.integration_type),
        status: integration.status,
        icon: getIntegrationIcon(integration.integration_type),
        features: [],
        authType: 'oauth2',
        lastSync: integration.last_sync,
        config: integration.configuration ? JSON.parse(integration.configuration) : {},
        error_message: integration.error_message
      }));
      
      setUserIntegrations(convertedIntegrations);
    } catch (error) {
      console.error('Error fetching data:', error);
      setSnackbar({ open: true, message: 'Error loading integrations', severity: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const getCategoryByType = (type: string): string => {
    const categoryMap: Record<string, string> = {
      'salesforce': 'CRM',
      'hubspot': 'CRM',
      'pipedrive': 'CRM',
      'google_calendar': 'Calendar',
      'microsoft_outlook': 'Calendar',
      'calendly': 'Calendar',
      'slack': 'Communication',
      'microsoft_teams': 'Communication',
      'discord': 'Communication',
      'stripe': 'Payment',
      'square': 'Payment',
      'paypal': 'Payment',
      'google_analytics': 'Analytics',
      'mixpanel': 'Analytics',
      'shopify': 'E-commerce',
      'woocommerce': 'E-commerce'
    };
    return categoryMap[type] || 'Other';
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleConnectIntegration = async (integration: any) => {
    setSelectedIntegration(integration);
    
    if (integration.authType === 'oauth2') {
      // Start OAuth flow
      try {
        const oauthResponse = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/oauth/url`, {
          integration_id: integration.id,
          business_id: businessId,
          redirect_uri: `${window.location.origin}/integrations/oauth-callback`
        });

        if (oauthResponse.data.oauth_url) {
          window.location.href = oauthResponse.data.oauth_url;
        }
      } catch (error) {
        console.error('Error starting OAuth flow:', error);
        setSnackbar({ open: true, message: 'Error starting OAuth flow', severity: 'error' });
      }
    } else {
      // Show manual configuration dialog
      setConfigForm({});
      setConfigDialogOpen(true);
    }
  };

  const handleSaveConfiguration = async () => {
    if (!selectedIntegration || !businessId) return;

    try {
      const payload = {
        integration_type: selectedIntegration.type || selectedIntegration.id,
        integration_id: selectedIntegration.id,
        name: selectedIntegration.name,
        configuration: {},
        credentials: configForm
      };

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/business/${businessId}`,
        payload
      );

      setSnackbar({ 
        open: true, 
        message: `${selectedIntegration.name} connected successfully`, 
        severity: 'success' 
      });
      
      setConfigDialogOpen(false);
      setSelectedIntegration(null);
      fetchData();
    } catch (error) {
      console.error('Error saving configuration:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error connecting integration', 
        severity: 'error' 
      });
    }
  };

  const handleTestConnection = async (integration: Integration) => {
    if (!businessId) return;

    try {
      setTestingConnection(integration.id);
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/business/${businessId}/test/${integration.id}`,
        {
          credentials: integration.config,
          configuration: integration.config
        }
      );

      if (response.data.success) {
        setSnackbar({ 
          open: true, 
          message: `${integration.name} connection test successful`, 
          severity: 'success' 
        });
      } else {
        setSnackbar({ 
          open: true, 
          message: `Connection test failed: ${response.data.error}`, 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error testing connection', 
        severity: 'error' 
      });
    } finally {
      setTestingConnection(null);
    }
  };

  const handleSyncIntegration = async (integration: Integration) => {
    if (!businessId) return;

    try {
      setSyncing(integration.id);
      
      // Find the database integration ID
      const userIntegration = userIntegrations.find(ui => ui.id === integration.id);
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/business/${businessId}/sync/${userIntegration?.id || integration.id}`
      );

      if (response.data.success) {
        setSnackbar({ 
          open: true, 
          message: `${integration.name} sync completed successfully`, 
          severity: 'success' 
        });
        fetchData(); // Refresh to update last sync time
      } else {
        setSnackbar({ 
          open: true, 
          message: `Sync failed: ${response.data.error}`, 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Error syncing integration:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error syncing integration', 
        severity: 'error' 
      });
    } finally {
      setSyncing(null);
    }
  };

  const handleDisconnectIntegration = async (integrationId: string) => {
    if (!businessId) return;

    try {
      // Find the user integration
      const userIntegration = userIntegrations.find(ui => ui.id === integrationId);
      if (!userIntegration) return;

      await axios.delete(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/integrations/business/${businessId}/integration/${userIntegration.id}`
      );

      setSnackbar({ 
        open: true, 
        message: 'Integration disconnected successfully', 
        severity: 'success' 
      });
      
      fetchData();
    } catch (error) {
      console.error('Error disconnecting integration:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error disconnecting integration', 
        severity: 'error' 
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'success';
      case 'error': return 'error';
      case 'connecting': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircleIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'connecting': return <SyncIcon color="warning" />;
      default: return <SettingsIcon color="action" />;
    }
  };

  const isIntegrationConnected = (integrationId: string) => {
    return userIntegrations.some(ui => ui.id === integrationId && ui.status === 'connected');
  };

  const getUserIntegration = (integrationId: string) => {
    return userIntegrations.find(ui => ui.id === integrationId);
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Integrations
        </Typography>
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
          Connect your AI receptionist with your favorite business tools and automate your workflows
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
                {userIntegrations.filter(i => i.status === 'connected').length}
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
                {integrationTypes.reduce((total, type) => total + type.integrations.length, 0)}
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
                {userIntegrations.filter(i => i.status === 'connecting').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Setting Up
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
                {userIntegrations.filter(i => i.status === 'error').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Errors
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="All Integrations" />
        <Tab label="Connected" />
        <Tab label="Popular" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* All Integrations */}
        {integrationTypes.map((category) => (
          <Card key={category.type} sx={{ mb: 3 }}>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h5">{category.name}</Typography>
                  <Chip 
                    label={`${category.integrations.length} available`} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                </Box>
              }
              subheader={category.description}
            />
            <CardContent>
              <Grid container spacing={3}>
                {category.integrations.map((integration) => {
                  const userIntegration = getUserIntegration(integration.id);
                  const isConnected = isIntegrationConnected(integration.id);
                  
                  return (
                    <Grid item xs={12} md={6} lg={4} key={integration.id}>
                      <Card variant="outlined" sx={{ height: '100%', position: 'relative' }}>
                        {isConnected && (
                          <Badge
                            badgeContent={<CheckCircleIcon sx={{ fontSize: 16 }} />}
                            color="success"
                            sx={{ 
                              position: 'absolute', 
                              top: 16, 
                              right: 16, 
                              zIndex: 1 
                            }}
                          />
                        )}
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                              {getIntegrationIcon(integration.icon)}
                            </Avatar>
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography variant="h6">{integration.name}</Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {userIntegration && getStatusIcon(userIntegration.status)}
                                <Chip
                                  label={isConnected ? 'CONNECTED' : 'AVAILABLE'}
                                  color={getStatusColor(userIntegration?.status || 'default') as any}
                                  size="small"
                                />
                              </Box>
                            </Box>
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {integration.description}
                          </Typography>

                          {userIntegration?.error_message && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                              {userIntegration.error_message}
                            </Alert>
                          )}
                          
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" gutterBottom>Features:</Typography>
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {integration.features.slice(0, 3).map((feature, index) => (
                                <Chip key={index} label={feature} size="small" variant="outlined" />
                              ))}
                            </Box>
                          </Box>

                          {userIntegration?.lastSync && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                              Last synced: {new Date(userIntegration.lastSync).toLocaleString()}
                            </Typography>
                          )}

                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {!isConnected ? (
                              <Button
                                variant="contained"
                                onClick={() => handleConnectIntegration(integration)}
                                startIcon={integration.authType === 'oauth2' ? <LaunchIcon /> : <SettingsIcon />}
                                fullWidth
                              >
                                Connect
                              </Button>
                            ) : (
                              <>
                                <Button
                                  variant="outlined"
                                  onClick={() => handleTestConnection(userIntegration)}
                                  disabled={testingConnection === integration.id}
                                  startIcon={testingConnection === integration.id ? <SyncIcon className="animate-spin" /> : <RefreshIcon />}
                                  size="small"
                                >
                                  Test
                                </Button>
                                <Button
                                  variant="outlined"
                                  onClick={() => handleSyncIntegration(userIntegration)}
                                  disabled={syncing === integration.id}
                                  startIcon={syncing === integration.id ? <SyncIcon className="animate-spin" /> : <SyncIcon />}
                                  size="small"
                                >
                                  Sync
                                </Button>
                                <Button
                                  variant="outlined"
                                  color="error"
                                  onClick={() => handleDisconnectIntegration(integration.id)}
                                  size="small"
                                >
                                  Disconnect
                                </Button>
                              </>
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            </CardContent>
          </Card>
        ))}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Connected Integrations */}
        <Grid container spacing={3}>
          {userIntegrations
            .filter(integration => integration.status === 'connected')
            .map((integration) => (
              <Grid item xs={12} md={6} lg={4} key={integration.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                        {integration.icon}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6">{integration.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {integration.category}
                        </Typography>
                      </Box>
                      <CheckCircleIcon color="success" />
                    </Box>

                    {integration.lastSync && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                        Last synced: {new Date(integration.lastSync).toLocaleString()}
                      </Typography>
                    )}

                    <Stack direction="row" spacing={1}>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleSyncIntegration(integration)}
                        disabled={syncing === integration.id}
                        startIcon={<SyncIcon />}
                      >
                        Sync Now
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          setSelectedIntegration(integration);
                          setConfigForm(integration.config || {});
                          setConfigDialogOpen(true);
                        }}
                        startIcon={<SettingsIcon />}
                      >
                        Configure
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
          ))}
          
          {userIntegrations.filter(i => i.status === 'connected').length === 0 && (
            <Grid item xs={12}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <CloudIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  No connected integrations
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Connect your favorite business tools to automate workflows and sync data
                </Typography>
                <Button variant="contained" onClick={() => setTabValue(0)}>
                  Browse Integrations
                </Button>
              </Paper>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Popular Integrations */}
        <Grid container spacing={3}>
          {integrationTypes
            .flatMap(type => type.integrations)
            .filter(integration => ['salesforce', 'hubspot', 'google_calendar', 'slack', 'stripe'].includes(integration.id))
            .map((integration) => {
              const userIntegration = getUserIntegration(integration.id);
              const isConnected = isIntegrationConnected(integration.id);
              
              return (
                <Grid item xs={12} md={6} lg={4} key={integration.id}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                          {getIntegrationIcon(integration.icon)}
                        </Avatar>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="h6">{integration.name}</Typography>
                          <Chip
                            label={isConnected ? 'CONNECTED' : 'POPULAR'}
                            color={isConnected ? 'success' : 'warning'}
                            size="small"
                          />
                        </Box>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {integration.description}
                      </Typography>

                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 2 }}>
                        {integration.features.slice(0, 2).map((feature, index) => (
                          <Chip key={index} label={feature} size="small" variant="outlined" />
                        ))}
                      </Box>

                      <Button
                        variant={isConnected ? 'outlined' : 'contained'}
                        onClick={() => isConnected ? handleSyncIntegration(userIntegration!) : handleConnectIntegration(integration)}
                        fullWidth
                        startIcon={isConnected ? <SyncIcon /> : <LaunchIcon />}
                      >
                        {isConnected ? 'Sync Now' : 'Connect'}
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
        </Grid>
      </TabPanel>

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
                To connect {selectedIntegration.name}, please provide your API credentials. 
                Your credentials are encrypted and stored securely.
              </Alert>
              
              {selectedIntegration.id === 'pipedrive' && (
                <Box>
                  <TextField
                    fullWidth
                    label="Company Domain"
                    variant="outlined"
                    margin="normal"
                    placeholder="your-company"
                    helperText="Your Pipedrive domain (without .pipedrive.com)"
                    value={configForm.company_domain || ''}
                    onChange={(e) => setConfigForm({ ...configForm, company_domain: e.target.value })}
                  />
                  <TextField
                    fullWidth
                    label="API Token"
                    variant="outlined"
                    margin="normal"
                    type="password"
                    helperText="Get this from your Pipedrive settings"
                    value={configForm.api_token || ''}
                    onChange={(e) => setConfigForm({ ...configForm, api_token: e.target.value })}
                  />
                </Box>
              )}

              {selectedIntegration.id === 'stripe' && (
                <Box>
                  <TextField
                    fullWidth
                    label="Publishable Key"
                    variant="outlined"
                    margin="normal"
                    placeholder="pk_test_..."
                    helperText="Your Stripe publishable key"
                    value={configForm.publishable_key || ''}
                    onChange={(e) => setConfigForm({ ...configForm, publishable_key: e.target.value })}
                  />
                  <TextField
                    fullWidth
                    label="Secret Key"
                    variant="outlined"
                    margin="normal"
                    type="password"
                    placeholder="sk_test_..."
                    helperText="Your Stripe secret key"
                    value={configForm.secret_key || ''}
                    onChange={(e) => setConfigForm({ ...configForm, secret_key: e.target.value })}
                  />
                </Box>
              )}

              {selectedIntegration.authType === 'webhook' && (
                <Box>
                  <TextField
                    fullWidth
                    label="Webhook URL"
                    variant="outlined"
                    margin="normal"
                    value={configForm.webhook_url || ''}
                    onChange={(e) => setConfigForm({ ...configForm, webhook_url: e.target.value })}
                    helperText="The webhook URL for this integration"
                  />
                  <TextField
                    fullWidth
                    label="Secret Token (Optional)"
                    variant="outlined"
                    margin="normal"
                    type="password"
                    value={configForm.secret_token || ''}
                    onChange={(e) => setConfigForm({ ...configForm, secret_token: e.target.value })}
                    helperText="Secret token for webhook verification"
                  />
                </Box>
              )}

              {!['pipedrive', 'stripe'].includes(selectedIntegration.id) && selectedIntegration.authType === 'api_key' && (
                <Box>
                  <TextField
                    fullWidth
                    label="API Key"
                    variant="outlined"
                    margin="normal"
                    type="password"
                    value={configForm.api_key || ''}
                    onChange={(e) => setConfigForm({ ...configForm, api_key: e.target.value })}
                    helperText={`Get this from your ${selectedIntegration.name} settings`}
                  />
                  <TextField
                    fullWidth
                    label="API Secret (if required)"
                    variant="outlined"
                    margin="normal"
                    type="password"
                    value={configForm.api_secret || ''}
                    onChange={(e) => setConfigForm({ ...configForm, api_secret: e.target.value })}
                  />
                </Box>
              )}

              <Divider sx={{ my: 3 }} />
              
              <Typography variant="h6" gutterBottom>Features Enabled</Typography>
              <List>
                {selectedIntegration.features.map((feature: string, index: number) => (
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
          <Button variant="contained" onClick={handleSaveConfiguration}>
            Connect Integration
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