'use client';
import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Slider from '@mui/material/Slider';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import IconButton from '@mui/material/IconButton';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import CircularProgress from '@mui/material/CircularProgress';
import Chip from '@mui/material/Chip';
import InputAdornment from '@mui/material/InputAdornment';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ContentCopy from '@mui/icons-material/ContentCopy';
import Refresh from '@mui/icons-material/Refresh';
import CheckCircle from '@mui/icons-material/CheckCircle';
import Cancel from '@mui/icons-material/Cancel';
import Person from '@mui/icons-material/Person';
import Notifications from '@mui/icons-material/Notifications';
import VpnKey from '@mui/icons-material/VpnKey';
import Tune from '@mui/icons-material/Tune';
import MenuItem from '@mui/material/MenuItem';
import Save from '@mui/icons-material/Save';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

interface NotificationPreferences {
  emailMissedCalls: boolean;
  emailDailySummary: boolean;
  emailAppointmentReminders: boolean;
  smsMissedCalls: boolean;
  smsNewAppointments: boolean;
}

interface BusinessConfig {
  autonomyLevel: number;
  confidenceThreshold: number;
  maxCallDuration: number;
}

interface IntegrationStatus {
  twilio: { connected: boolean; details: string };
  email: { connected: boolean; details: string };
}

interface Business {
  id: number;
  name: string;
  type: string;
  language: string;
  phone: string;
  address: string;
  settings: any;
}

interface SnackbarState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'info' | 'warning';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const LANGUAGES = [
  { code: 'en-US', label: 'English (US)' },
  { code: 'en-GB', label: 'English (UK)' },
  { code: 'es-US', label: 'Spanish (US)' },
  { code: 'es-ES', label: 'Spanish (Spain)' },
  { code: 'fr-FR', label: 'French' },
  { code: 'de-DE', label: 'German' },
  { code: 'it-IT', label: 'Italian' },
  { code: 'ja-JP', label: 'Japanese' },
  { code: 'ko-KR', label: 'Korean' },
  { code: 'pt-BR', label: 'Portuguese' },
  { code: 'zh-CN', label: 'Chinese (Mandarin)' },
  { code: 'auto', label: 'Auto-Detect (Experimental)' },
];

export default function SettingsPage() {
  const { user, isAuthenticated } = useAuth();

  // Business data
  const [business, setBusiness] = useState<Business | null>(null);
  const [savingBusiness, setSavingBusiness] = useState(false);

  // Profile / Password
  const [userEmail, setUserEmail] = useState<string>('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  // Notification preferences
  const [notifications, setNotifications] = useState<NotificationPreferences>({
    emailMissedCalls: true,
    emailDailySummary: true,
    emailAppointmentReminders: true,
    smsMissedCalls: false,
    smsNewAppointments: false,
  });

  // API Keys & Integration Status
  const [apiKey, setApiKey] = useState('sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus>({
    twilio: { connected: false, details: 'Checking...' },
    email: { connected: false, details: 'Checking...' },
  });
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false);

  // Business Configuration
  const [businessConfig, setBusinessConfig] = useState<BusinessConfig>({
    autonomyLevel: 70,
    confidenceThreshold: 80,
    maxCallDuration: 300,
  });

  // UI State
  const [isLoading, setIsLoading] = useState(true);
  const [savingNotifications, setSavingNotifications] = useState(false);
  const [savingBusinessConfig, setSavingBusinessConfig] = useState(false);
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'success',
  });

  // ---------------------------------------------------------------------------
  // Data Fetching
  // ---------------------------------------------------------------------------

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await api.get('/auth/me');
      setUserEmail(response.data.email || '');
    } catch (error) {
      console.warn('Settings: failed to fetch user profile', error);
      // Fallback to AuthContext user if available
      if (user?.email) {
        setUserEmail(user.email);
      }
    }
  }, [user]);

  const fetchIntegrationStatus = useCallback(async () => {
    const [twilioResult, emailResult] = await Promise.allSettled([
      api.get('/sms/status'),
      api.get('/email/status'),
    ]);

    setIntegrationStatus({
      twilio:
        twilioResult.status === 'fulfilled'
          ? {
              connected: twilioResult.value.data?.configured ?? twilioResult.value.data?.connected ?? false,
              details: twilioResult.value.data?.phone_number || twilioResult.value.data?.details || 'Configured',
            }
          : { connected: false, details: 'Unable to reach service' },
      email:
        emailResult.status === 'fulfilled'
          ? {
              connected: emailResult.value.data?.configured ?? emailResult.value.data?.connected ?? false,
              details: emailResult.value.data?.provider || emailResult.value.data?.details || 'Configured',
            }
          : { connected: false, details: 'Unable to reach service' },
    });
  }, []);

  const fetchBusiness = useCallback(async () => {
    try {
      const response = await api.get('/businesses/');
      if (response.data && response.data.length > 0) {
        setBusiness(response.data[0]);
        const b = response.data[0];
        if (b.settings) {
          setBusinessConfig(prev => ({
            ...prev,
            ...b.settings
          }));
        }
      }
    } catch (error) {
      console.warn('Settings: failed to fetch business', error);
    }
  }, []);

  const handleSaveBusiness = async () => {
    if (!business) return;
    setSavingBusiness(true);
    try {
      // Sync local businessConfig into settings JSON
      const updatedSettings = {
        ...(business.settings || {}),
        ...businessConfig
      };

      await api.put(`/businesses/${business.id}`, {
        ...business,
        settings: updatedSettings
      });
      showSnackbar('Business settings saved successfully.');
    } catch (error) {
      showSnackbar('Failed to save business settings.', 'error');
    } finally {
      setSavingBusiness(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;

    const loadAll = async () => {
      setIsLoading(true);
      await Promise.allSettled([
        fetchUserProfile(),
        fetchIntegrationStatus(),
        fetchBusiness()
      ]);
      setIsLoading(false);
    };

    loadAll();
  }, [isAuthenticated, fetchUserProfile, fetchIntegrationStatus, fetchBusiness]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const showSnackbar = (message: string, severity: SnackbarState['severity'] = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  // -- Password --

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');

    if (!currentPassword) {
      setPasswordError('Current password is required.');
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }

    // UI-only: show success snackbar
    showSnackbar('Password updated successfully.');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  // -- Notifications --

  const handleNotificationToggle = (key: keyof NotificationPreferences) => {
    setNotifications((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSaveNotifications = async () => {
    setSavingNotifications(true);
    // Simulate a short delay for UX feedback
    await new Promise((r) => setTimeout(r, 600));
    setSavingNotifications(false);
    showSnackbar('Notification preferences saved.');
  };

  // -- API Key --

  const handleCopyApiKey = async () => {
    try {
      await navigator.clipboard.writeText(apiKey);
      showSnackbar('API key copied to clipboard.', 'info');
    } catch {
      showSnackbar('Failed to copy API key.', 'error');
    }
  };

  const handleRegenerateKey = () => {
    // Generate a pseudo-random key for demonstration purposes
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    const segment = (len: number) =>
      Array.from({ length: len }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
    const newKey = `sk-${segment(4)}-${segment(4)}-${segment(4)}-${segment(12)}`;
    setApiKey(newKey);
    setRegenerateDialogOpen(false);
    showSnackbar('API key regenerated. Make sure to update your integrations.', 'warning');
  };

  // -- Business Config --

  const handleSaveBusinessConfig = async () => {
    setSavingBusinessConfig(true);
    await new Promise((r) => setTimeout(r, 600));
    setSavingBusinessConfig(false);
    showSnackbar('Business configuration saved.');
  };

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const maskApiKey = (key: string): string => {
    if (key.length <= 8) return key;
    return key.slice(0, 7) + '*'.repeat(key.length - 11) + key.slice(-4);
  };

  // ---------------------------------------------------------------------------
  // Loading State
  // ---------------------------------------------------------------------------

  if (isLoading && isAuthenticated) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 }, px: { xs: 2, sm: 3 } }}>
      {/* Page Header */}
      <Box sx={{ mb: { xs: 3, sm: 4 } }}>
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          sx={{
            fontWeight: 'bold',
            color: 'primary.main',
            fontSize: { xs: '1.75rem', sm: '2.125rem' },
          }}
        >
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          Manage your account, notifications, integrations, and AI configuration.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* ================================================================= */}
        {/* 1. PROFILE SETTINGS                                              */}
        {/* ================================================================= */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Person color="primary" />}
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Profile Settings
                </Typography>
              }
              subheader="Manage your account information and password"
            />
            <Divider />
            <CardContent>
              {/* Email Display */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                  Email Address
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {userEmail || user?.email || 'Not available'}
                </Typography>
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Password Change Form */}
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                Change Password
              </Typography>

              {passwordError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {passwordError}
                </Alert>
              )}

              <Box component="form" onSubmit={handlePasswordSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Current Password"
                      type={showCurrentPassword ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      size="small"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                              edge="end"
                              aria-label={showCurrentPassword ? 'Hide current password' : 'Show current password'}
                            >
                              {showCurrentPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="New Password"
                      type={showNewPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      size="small"
                      helperText="Minimum 8 characters"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => setShowNewPassword(!showNewPassword)}
                              edge="end"
                              aria-label={showNewPassword ? 'Hide new password' : 'Show new password'}
                            >
                              {showNewPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Confirm New Password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      size="small"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                              edge="end"
                              aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                            >
                              {showConfirmPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Button type="submit" variant="contained" size="small">
                      Update Password
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ================================================================= */}
        {/* 2. NOTIFICATION PREFERENCES                                      */}
        {/* ================================================================= */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Notifications color="primary" />}
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Notification Preferences
                </Typography>
              }
              subheader="Choose how and when you want to be notified"
            />
            <Divider />
            <CardContent>
              <Grid container spacing={3}>
                {/* Email Notifications */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    Email Notifications
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={notifications.emailMissedCalls}
                          onChange={() => handleNotificationToggle('emailMissedCalls')}
                          color="primary"
                        />
                      }
                      label="Missed calls"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={notifications.emailDailySummary}
                          onChange={() => handleNotificationToggle('emailDailySummary')}
                          color="primary"
                        />
                      }
                      label="Daily summary"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={notifications.emailAppointmentReminders}
                          onChange={() => handleNotificationToggle('emailAppointmentReminders')}
                          color="primary"
                        />
                      }
                      label="Appointment reminders"
                    />
                  </Box>
                </Grid>

                {/* SMS Notifications */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    SMS Notifications
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={notifications.smsMissedCalls}
                          onChange={() => handleNotificationToggle('smsMissedCalls')}
                          color="primary"
                        />
                      }
                      label="Missed calls"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={notifications.smsNewAppointments}
                          onChange={() => handleNotificationToggle('smsNewAppointments')}
                          color="primary"
                        />
                      }
                      label="New appointments"
                    />
                  </Box>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  startIcon={savingNotifications ? <CircularProgress size={16} color="inherit" /> : <Save />}
                  onClick={handleSaveNotifications}
                  disabled={savingNotifications}
                  size="small"
                >
                  {savingNotifications ? 'Saving...' : 'Save Preferences'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ================================================================= */}
        {/* 3. API KEYS                                                      */}
        {/* ================================================================= */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<VpnKey color="primary" />}
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  API Keys
                </Typography>
              }
              subheader="Manage your API key and view integration statuses"
            />
            <Divider />
            <CardContent>
              {/* API Key Display */}
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                Your API Key
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: 'grey.100',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  mb: 2,
                  flexWrap: { xs: 'wrap', sm: 'nowrap' },
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    fontFamily: 'monospace',
                    flexGrow: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    letterSpacing: '0.02em',
                  }}
                >
                  {maskApiKey(apiKey)}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
                  <IconButton size="small" onClick={handleCopyApiKey} aria-label="Copy API key">
                    <ContentCopy fontSize="small" />
                  </IconButton>
                  <Button
                    size="small"
                    variant="outlined"
                    color="warning"
                    startIcon={<Refresh fontSize="small" />}
                    onClick={() => setRegenerateDialogOpen(true)}
                  >
                    Regenerate Key
                  </Button>
                </Box>
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Integration Status */}
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                Integration Status
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 2,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: integrationStatus.twilio.connected ? 'success.light' : 'grey.300',
                    }}
                  >
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        Twilio (SMS)
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {integrationStatus.twilio.details}
                      </Typography>
                    </Box>
                    <Chip
                      icon={integrationStatus.twilio.connected ? <CheckCircle /> : <Cancel />}
                      label={integrationStatus.twilio.connected ? 'Connected' : 'Disconnected'}
                      color={integrationStatus.twilio.connected ? 'success' : 'default'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 2,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: integrationStatus.email.connected ? 'success.light' : 'grey.300',
                    }}
                  >
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        Email
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {integrationStatus.email.details}
                      </Typography>
                    </Box>
                    <Chip
                      icon={integrationStatus.email.connected ? <CheckCircle /> : <Cancel />}
                      label={integrationStatus.email.connected ? 'Connected' : 'Disconnected'}
                      color={integrationStatus.email.connected ? 'success' : 'default'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* ================================================================= */}
        {/* 4. BUSINESS CONFIGURATION                                        */}
        {/* ================================================================= */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Tune color="primary" />}
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Business Configuration
                </Typography>
              }
              subheader="Fine-tune AI behavior and call handling parameters"
            />
            <Divider />
            <CardContent>
              <Grid container spacing={4}>
                {/* Language Configuration */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ pr: { md: 2 } }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      AI Response Language
                    </Typography>
                    <TextField
                      select
                      fullWidth
                      size="small"
                      value={business?.settings?.language || 'en-US'}
                      onChange={(e) => {
                        if (business) {
                          setBusiness({ 
                            ...business, 
                            settings: { 
                              ...(business.settings || {}), 
                              language: e.target.value 
                            } 
                          });
                        }
                      }}
                      helperText="The language the AI will use to respond to customers"
                    >
                      {LANGUAGES.map((option) => (
                        <MenuItem key={option.code} value={option.code}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Box>
                </Grid>

                {/* AI Autonomy Level */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ pl: { md: 2 } }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        AI Autonomy Level
                      </Typography>
                      <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
                        {businessConfig.autonomyLevel}%
                      </Typography>
                    </Box>
                    <Slider
                      value={businessConfig.autonomyLevel}
                      onChange={(_, value) =>
                        setBusinessConfig((prev) => ({ ...prev, autonomyLevel: value as number }))
                      }
                      min={0}
                      max={100}
                      step={5}
                      marks={[
                        { value: 0, label: '0%' },
                        { value: 50, label: '50%' },
                        { value: 100, label: '100%' },
                      ]}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(v) => `${v}%`}
                    />
                    <Typography variant="caption" color="text.secondary">
                      Higher values allow the AI to handle more decisions without human approval.
                    </Typography>
                  </Box>
                </Grid>

                {/* AI Confidence Threshold */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ pr: { md: 2 } }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        AI Confidence Threshold
                      </Typography>
                      <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
                        {businessConfig.confidenceThreshold}%
                      </Typography>
                    </Box>
                    <Slider
                      value={businessConfig.confidenceThreshold}
                      onChange={(_, value) =>
                        setBusinessConfig((prev) => ({ ...prev, confidenceThreshold: value as number }))
                      }
                      min={0}
                      max={100}
                      step={5}
                      marks={[
                        { value: 0, label: '0%' },
                        { value: 50, label: '50%' },
                        { value: 100, label: '100%' },
                      ]}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(v) => `${v}%`}
                    />
                    <Typography variant="caption" color="text.secondary">
                      Minimum confidence required before the AI acts autonomously on a decision.
                    </Typography>
                  </Box>
                </Grid>

                {/* Max Call Duration */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ pl: { md: 2 } }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      Max Call Duration
                    </Typography>
                    <TextField
                      fullWidth
                      type="number"
                      size="small"
                      value={businessConfig.maxCallDuration}
                      onChange={(e) => {
                        const val = parseInt(e.target.value, 10);
                        if (!isNaN(val) && val >= 0) {
                          setBusinessConfig((prev) => ({ ...prev, maxCallDuration: val }));
                        }
                      }}
                      InputProps={{
                        endAdornment: <InputAdornment position="end">seconds</InputAdornment>,
                        inputProps: { min: 0, max: 3600 },
                      }}
                      helperText={`Approximately ${Math.floor(businessConfig.maxCallDuration / 60)} min ${businessConfig.maxCallDuration % 60} sec`}
                    />
                  </Box>
                </Grid>
              </Grid>

              <Box sx={{ mt: 4 }}>
                <Button
                  variant="contained"
                  startIcon={savingBusiness ? <CircularProgress size={16} color="inherit" /> : <Save />}
                  onClick={handleSaveBusiness}
                  disabled={savingBusiness || !business}
                  size="small"
                >
                  {savingBusiness ? 'Saving...' : 'Save Configuration'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ================================================================= */}
      {/* REGENERATE API KEY CONFIRMATION DIALOG                            */}
      {/* ================================================================= */}
      <Dialog
        open={regenerateDialogOpen}
        onClose={() => setRegenerateDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 'bold' }}>Regenerate API Key?</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            This will invalidate your current API key immediately. Any services or integrations
            using the current key will stop working until you update them with the new key.
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone.
          </Alert>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setRegenerateDialogOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleRegenerateKey} variant="contained" color="warning">
            Regenerate
          </Button>
        </DialogActions>
      </Dialog>

      {/* ================================================================= */}
      {/* SNACKBAR                                                          */}
      {/* ================================================================= */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
