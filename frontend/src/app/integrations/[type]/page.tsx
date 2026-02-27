'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import api from '@/services/api';

interface IntegrationData {
  id?: number;
  name: string;
  integration_type: string;
  status: string;
  configuration: any;
  credentials?: any;
  error_message?: string;
}

export default function IntegrationConfigPage() {
  const params = useParams();
  const router = useRouter();
  const type = params.type as string; 
  
  const getDisplayType = () => {
    if (type === 'square_pos') return 'Square POS';
    if (type === 'hubspot_crm') return 'HubSpot CRM';
    return type.toUpperCase();
  };

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [integration, setIntegration] = useState<IntegrationData>({
    name: '',
    integration_type: '',
    status: 'pending',
    configuration: {},
    credentials: { api_key: '', access_token: '', location_id: '' }
  });

  useEffect(() => {
    fetchIntegration();
  }, [type]);

  const fetchIntegration = async () => {
    try {
      setLoading(true);
      const response = await api.get('/integrations');
      const existing = response.data.find((i: any) => i.integration_type === type);
      if (existing) {
        setIntegration(existing);
      } else {
        // Initialize with default for this type
        setIntegration({
          name: `${getDisplayType()}`,
          integration_type: type,
          status: 'pending',
          configuration: {},
          credentials: { api_key: '', access_token: '', location_id: '' }
        });
      }
    } catch (err: any) {
      console.error('Error fetching integration:', err);
      setError('Failed to load integration settings.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');
      
      let response;
      if (integration.id) {
        response = await api.put(`/integrations/${integration.id}`, integration);
      } else {
        response = await api.post('/integrations', integration);
      }
      
      setIntegration(response.data);
      if (response.data.status === 'active') {
        setSuccess('Integration successfully configured and active!');
      } else {
        setError(`Integration configured but connection failed: ${response.data.error_message || 'Unknown error'}`);
      }
    } catch (err: any) {
      console.error('Error saving integration:', err);
      setError(err.response?.data?.detail || 'Failed to save integration settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!integration.id) return;
    if (!window.confirm('Are you sure you want to delete this integration?')) return;

    try {
      setSaving(true);
      await api.delete(`/integrations/${integration.id}`);
      router.push('/integrations');
    } catch (err: any) {
      setError('Failed to delete integration.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Breadcrumbs 
        separator={<NavigateNextIcon fontSize="small" />} 
        aria-label="breadcrumb"
        sx={{ mb: 3 }}
      >
        <Link underline="hover" color="inherit" href="/integrations">
          Integrations Hub
        </Link>
        <Typography color="text.primary">{type.toUpperCase()} Configuration</Typography>
      </Breadcrumbs>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {getDisplayType()} Integration
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure how your AI receptionist interacts with your {getDisplayType()} system.
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

      <Card variant="outlined">
        <CardContent>
          <Box component="form" sx={{ '& > :not(style)': { mb: 3 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                Status: 
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {integration.status === 'active' ? (
                  <>
                    <CheckCircleIcon color="success" />
                    <Typography color="success.main">Active & Connected</Typography>
                  </>
                ) : (
                  <>
                    <ErrorIcon color="error" />
                    <Typography color="error.main">{integration.status === 'pending' ? 'Pending Configuration' : 'Connection Failed'}</Typography>
                  </>
                )}
              </Box>
            </Box>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Integration Name</label>
              <input 
                type="text"
                value={integration.name}
                onChange={(e) => setIntegration({ ...integration, name: e.target.value })}
                placeholder="e.g., Main POS System"
                style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Provider Type</label>
              <select 
                value={integration.integration_type}
                onChange={(e) => setIntegration({ ...integration, integration_type: e.target.value })}
                style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value="">Select a provider</option>
                {type === 'pos' ? (
                  <>
                    <option value="mock_pos">Mock POS (Demo Mode)</option>
                    <option value="clover">Clover</option>
                    <option value="square">Square</option>
                    <option value="toast">Toast</option>
                  </>
                ) : (
                  <>
                    <option value="mock_pms">Mock PMS (Demo Mode)</option>
                    <option value="opera">Oracle Opera</option>
                    <option value="cloudbeds">Cloudbeds</option>
                    <option value="mews">Mews</option>
                  </>
                )}
              </select>
            </div>

            {type === 'square_pos' ? (
              <>
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Square Access Token</label>
                  <input 
                    type="password"
                    value={integration.credentials?.access_token || ''}
                    onChange={(e) => setIntegration({ 
                      ...integration, 
                      credentials: { ...integration.credentials, access_token: e.target.value } 
                    })}
                    placeholder="EAAA..."
                    style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }}
                  />
                </div>
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Location ID</label>
                  <input 
                    type="text"
                    value={integration.credentials?.location_id || ''}
                    onChange={(e) => setIntegration({ 
                      ...integration, 
                      credentials: { ...integration.credentials, location_id: e.target.value } 
                    })}
                    placeholder="L..."
                    style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }}
                  />
                </div>
              </>
            ) : (
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  {type === 'hubspot_crm' ? 'HubSpot API Key' : 'API Key / Credentials'}
                </label>
                <input 
                  type="password"
                  value={integration.credentials?.api_key || ''}
                  onChange={(e) => setIntegration({ 
                    ...integration, 
                    credentials: { ...integration.credentials, api_key: e.target.value } 
                  })}
                  placeholder="Enter your API key"
                  style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>
            )}

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', mt: 4 }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button 
                  variant="contained" 
                  startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => router.push('/integrations')}
                >
                  Cancel
                </Button>
              </Box>
              
              {integration.id && (
                <Button 
                  color="error" 
                  startIcon={<DeleteIcon />}
                  onClick={handleDelete}
                  disabled={saving}
                >
                  Delete
                </Button>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}
