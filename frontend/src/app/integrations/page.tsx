'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Alert from '@mui/material/Alert';
import Skeleton from '@mui/material/Skeleton';
import Phone from '@mui/icons-material/Phone';
import Email from '@mui/icons-material/Email';
import CalendarMonth from '@mui/icons-material/CalendarMonth';
import Payment from '@mui/icons-material/Payment';
import Storage from '@mui/icons-material/Storage';
import Webhook from '@mui/icons-material/Webhook';
import HubIcon from '@mui/icons-material/Hub';
import BusinessIcon from '@mui/icons-material/Business';
import StoreIcon from '@mui/icons-material/Store';
import api from '@/services/api';

type IntegrationStatus = 'connected' | 'not_configured' | 'error' | 'loading';

interface IntegrationCardData {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: IntegrationStatus;
  statusLabel: string;
  actionLabel: string;
  route: string;
  color: string;
}

function getChipProps(status: IntegrationStatus): {
  label: string;
  color: 'success' | 'default' | 'error' | 'info';
} {
  switch (status) {
    case 'connected':
      return { label: 'Connected', color: 'success' };
    case 'not_configured':
      return { label: 'Not Configured', color: 'default' };
    case 'error':
      return { label: 'Error', color: 'error' };
    case 'loading':
      return { label: 'Checking...', color: 'info' };
  }
}

function getActionLabel(status: IntegrationStatus, defaultLabel: string): string {
  switch (status) {
    case 'connected':
      return 'Manage';
    case 'not_configured':
      return 'Connect';
    case 'error':
      return 'Configure';
    case 'loading':
      return defaultLabel;
  }
}

export default function IntegrationsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [integrations, setIntegrations] = useState<IntegrationCardData[]>([]);

  useEffect(() => {
    fetchAllStatuses();
  }, []);

  const fetchAllStatuses = async () => {
    setLoading(true);
    setError('');

    const defaultIntegrations: IntegrationCardData[] = [
      {
        id: 'twilio',
        name: 'Twilio (Voice & SMS)',
        description: 'Send SMS messages and manage voice calls through Twilio.',
        icon: <Phone />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Configure',
        route: '/sms',
        color: '#e53935',
      },
      {
        id: 'email',
        name: 'Email (SMTP)',
        description: 'Send email notifications, call summaries, and appointment reminders.',
        icon: <Email />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Configure',
        route: '/email',
        color: '#1e88e5',
      },
      {
        id: 'calendar',
        name: 'Google Calendar',
        description: 'Sync appointments and manage scheduling with Google Calendar.',
        icon: <CalendarMonth />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Connect',
        route: '/calendar',
        color: '#43a047',
      },
      {
        id: 'stripe',
        name: 'Stripe (Payments)',
        description: 'Process payments and manage orders through Stripe integration.',
        icon: <Payment />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Configure',
        route: '/orders',
        color: '#6a1b9a',
      },
      {
        id: 'knowledge',
        name: 'Knowledge Base',
        description: 'Upload and manage documents to power AI-driven responses.',
        icon: <Storage />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Manage',
        route: '/knowledge-base',
        color: '#ef6c00',
      },
      {
        id: 'webhooks',
        name: 'Webhooks',
        description: 'Configure webhook endpoints to receive real-time event notifications.',
        icon: <Webhook />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Manage',
        route: '/webhooks',
        color: '#00838f',
      },
      {
        id: 'pos',
        name: 'Square POS',
        description: 'Sync your Square catalog and inject AI orders directly into your Point of Sale.',
        icon: <StoreIcon />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Configure',
        route: '/integrations/square_pos',
        color: '#2e7d32',
      },
      {
        id: 'crm',
        name: 'HubSpot CRM',
        description: 'Sync customer profiles and log AI call summaries to your HubSpot timeline.',
        icon: <HubIcon />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Connect',
        route: '/integrations/hubspot_crm',
        color: '#ff7a59',
      },
      {
        id: 'pms',
        name: 'Property Management (PMS)',
        description: 'Connect your hotel PMS to manage room availability and guest bookings.',
        icon: <BusinessIcon />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Configure',
        route: '/integrations/pms',
        color: '#0277bd',
      },
      {
        id: 'calendly',
        name: 'Calendly',
        description: 'Sync appointments and manage bookings with Calendly integration.',
        icon: <CalendarMonth />,
        status: 'loading',
        statusLabel: '',
        actionLabel: 'Connect',
        route: '/calendly',
        color: '#006BFF',
      },
    ];

    setIntegrations(defaultIntegrations);

    const results = await Promise.allSettled([
      api.get('/sms/status'),           // 0 - twilio
      api.get('/email/status'),         // 1 - email
      api.get('/calendar'),             // 2 - calendar (also used for calendly)
      api.get('/payments/status'),      // 3 - stripe
      api.get('/knowledge-base/documents'), // 4 - knowledge
      api.get('/webhooks'),             // 5 - webhooks
      api.get('/integrations'),         // 6 - POS and PMS (generic)
    ]);

    const updated = defaultIntegrations.map((integration) => {
      const copy = { ...integration };

      switch (integration.id) {
        case 'twilio': {
          const result = results[0];
          if (result?.status === 'fulfilled') {
            const data = result.value.data;
            const configured =
              data?.configured === true ||
              data?.twilio_configured === true ||
              data?.status === 'configured';
            copy.status = configured ? 'connected' : 'not_configured';
            copy.statusLabel = configured ? 'Configured' : 'Not Configured';
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
        case 'email': {
          const result = results[1];
          if (result?.status === 'fulfilled') {
            const data = result.value.data;
            const configured =
              data?.configured === true ||
              data?.smtp_configured === true ||
              data?.status === 'configured';
            copy.status = configured ? 'connected' : 'not_configured';
            copy.statusLabel = configured ? 'Configured' : 'Not Configured';
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
        case 'calendar': {
          const result = results[2];
          if (result?.status === 'fulfilled') {
            const data = result.value.data;
            const calendars = data?.integrations || data?.calendars || data || [];
            const count = Array.isArray(calendars) ? calendars.length : 0;
            copy.status = count > 0 ? 'connected' : 'not_configured';
            copy.statusLabel =
              count > 0 ? `${count} calendar${count !== 1 ? 's' : ''} connected` : 'Not Connected';
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Connected';
          }
          break;
        }
        case 'stripe': {
          const result = results[3];
          if (result?.status === 'fulfilled') {
            const data = result.value.data;
            const configured =
              data?.configured === true ||
              data?.stripe_configured === true ||
              data?.status === 'configured';
            copy.status = configured ? 'connected' : 'not_configured';
            copy.statusLabel = configured ? 'Configured' : 'Not Configured';
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
        case 'knowledge': {
          const result = results[4];
          if (result?.status === 'fulfilled') {
            const data = result.value.data;
            const docs = data?.documents || data || [];
            const count = Array.isArray(docs) ? docs.length : 0;
            copy.status = count > 0 ? 'connected' : 'not_configured';
            copy.statusLabel =
              count > 0 ? `${count} document${count !== 1 ? 's' : ''} uploaded` : 'No Documents';
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'No Documents';
          }
          break;
        }
        case 'webhooks': {
          const result = results[5];
          if (result?.status === 'fulfilled') {
            const data = result.value.data;
            const hooks = data?.webhooks || data || [];
            const count = Array.isArray(hooks) ? hooks.length : 0;
            copy.status = count > 0 ? 'connected' : 'not_configured';
            copy.statusLabel =
              count > 0 ? `${count} webhook${count !== 1 ? 's' : ''} active` : 'No Webhooks';
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'No Webhooks';
          }
          break;
        }
        case 'pos': {
          const result = results[6];
          if (result?.status === 'fulfilled' && Array.isArray(result.value.data)) {
            const pos = result.value.data.find((i: any) => i.integration_type?.includes('pos'));
            if (pos) {
              copy.status = pos.status === 'active' ? 'connected' : 'error';
              copy.statusLabel = pos.status === 'active' ? 'Connected' : 'Error';
            } else {
              copy.status = 'not_configured';
              copy.statusLabel = 'Not Configured';
            }
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
        case 'crm': {
          const result = results[6];
          if (result?.status === 'fulfilled' && Array.isArray(result.value.data)) {
            const crm = result.value.data.find((i: any) => 
              i.integration_type?.includes('hubspot') || i.integration_type?.includes('crm')
            );
            if (crm) {
              copy.status = crm.status === 'active' ? 'connected' : 'error';
              copy.statusLabel = crm.status === 'active' ? 'Connected' : 'Error';
            } else {
              copy.status = 'not_configured';
              copy.statusLabel = 'Not Configured';
            }
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
        case 'pms': {
          const result = results[6];
          if (result?.status === 'fulfilled' && Array.isArray(result.value.data)) {
            const pms = result.value.data.find((i: any) => i.integration_type?.includes('pms'));
            if (pms) {
              copy.status = pms.status === 'active' ? 'connected' : 'error';
              copy.statusLabel = pms.status === 'active' ? 'Connected' : 'Error';
            } else {
              copy.status = 'not_configured';
              copy.statusLabel = 'Not Configured';
            }
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
        case 'calendly': {
          // Check Calendly status from calendar endpoint (results[2])
          const result = results[2];
          if (result?.status === 'fulfilled') {
            const integrations = result.value.data?.integrations || [];
            const calendly = integrations.find((i: any) => i.provider === 'calendly');
            if (calendly) {
              copy.status = calendly.status === 'active' ? 'connected' : 'error';
              copy.statusLabel = calendly.status === 'active' ? 'Connected' : 'Expired';
            } else {
              copy.status = 'not_configured';
              copy.statusLabel = 'Not Configured';
            }
          } else {
            copy.status = 'not_configured';
            copy.statusLabel = 'Not Configured';
          }
          break;
        }
      }

      copy.actionLabel = getActionLabel(copy.status, integration.actionLabel);
      return copy;
    });

    setIntegrations(updated);
    setLoading(false);
  };

  const handleNavigate = (route: string) => {
    router.push(route);
  };

  const connectedCount = integrations.filter((i) => i.status === 'connected').length;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Integrations Hub
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Connect and manage your third-party services
        </Typography>
        {!loading && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {connectedCount} of {integrations.length} integrations connected
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(connectedCount / integrations.length) * 100}
              sx={{
                mt: 1,
                height: 6,
                borderRadius: 3,
                maxWidth: 300,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 3,
                  backgroundColor: 'success.main',
                },
              }}
            />
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Integration Cards Grid */}
      <Grid container spacing={3}>
        {integrations.map((integration) => {
          const chipProps = getChipProps(integration.status);

          return (
            <Grid item xs={12} sm={6} md={4} key={integration.id}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out',
                  '&:hover': {
                    boxShadow: 6,
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1, pb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: integration.color,
                        width: 48,
                        height: 48,
                      }}
                    >
                      {integration.icon}
                    </Avatar>
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="subtitle1" fontWeight={600} noWrap>
                        {integration.name}
                      </Typography>
                      {loading ? (
                        <Skeleton width={100} height={24} />
                      ) : (
                        <Chip
                          label={integration.statusLabel || chipProps.label}
                          color={chipProps.color}
                          size="small"
                          variant={integration.status === 'not_configured' ? 'outlined' : 'filled'}
                          sx={{ mt: 0.5 }}
                        />
                      )}
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                    {integration.description}
                  </Typography>
                </CardContent>

                <CardActions sx={{ px: 2, pb: 2, pt: 0 }}>
                  {loading ? (
                    <Skeleton width={80} height={36} />
                  ) : (
                    <Button
                      size="small"
                      variant={integration.status === 'connected' ? 'outlined' : 'contained'}
                      onClick={() => handleNavigate(integration.route)}
                      sx={{ textTransform: 'none' }}
                    >
                      {integration.actionLabel}
                    </Button>
                  )}
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Container>
  );
}
