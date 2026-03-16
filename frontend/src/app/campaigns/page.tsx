'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import CampaignIcon from '@mui/icons-material/Campaign';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import GroupIcon from '@mui/icons-material/Group';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { MetricCard } from '@/components/ui/MetricCard';
import api from '@/services/api';

interface OutboundStats {
  total_outbound_calls: number;
  successful_contacts: number;
  conversion_rate: number;
}

export default function CampaignsPage() {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [stats, setStats] = useState<OutboundStats>({
    total_outbound_calls: 0,
    successful_contacts: 0,
    conversion_rate: 0
  });
  const [businessId, setBusinessId] = useState<number | null>(null);
  
  // Custom Campaign Form
  const [briefing, setBriefing] = useState('');
  const [customerIds, setCustomerIds] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const bizResponse = await api.get('/businesses');
      if (bizResponse.data.length > 0) {
        const bid = bizResponse.data[0].id;
        setBusinessId(bid);
        const response = await api.get(`/campaigns/stats/overview?business_id=${bid}`);
        setStats(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch campaign stats');
    }
  };

  const handleTriggerReminders = async () => {
    if (!businessId) return;
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await api.post('/campaigns/trigger-reminders', { business_id: businessId });
      setSuccess(`Success! ${response.data.calls_triggered} reminder calls scheduled.`);
      fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to trigger reminders.');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerCustom = async () => {
    if (!businessId) return;
    if (!briefing) {
      setError('Please provide a briefing for the AI.');
      return;
    }
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const ids = customerIds.split(',').map(id => parseInt(ids.trim())).filter(id => !isNaN(id));
      await api.post('/campaigns/custom-outreach', {
        business_id: businessId,
        customer_ids: ids,
        briefing: briefing
      });
      setSuccess('Custom outreach campaign triggered successfully!');
      fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to trigger campaign.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={800} gutterBottom>
          AI Campaign Manager
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure and trigger proactive AI outreach to your customers.
        </Typography>
      </Box>

      {/* Stats Summary */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <MetricCard
            title="Total Outreach Calls"
            value={stats.total_outbound_calls}
            icon={<CampaignIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <MetricCard
            title="Successful Contacts"
            value={stats.successful_contacts}
            icon={<GroupIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <MetricCard
            title="Conversion Rate"
            value={`${stats.conversion_rate}%`}
            icon={<PlayArrowIcon />}
            color="info"
          />
        </Grid>
      </Grid>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

      <Card variant="outlined">
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tab} onChange={(_, v) => setTab(v)}>
            <Tab icon={<EventRepeatIcon />} label="Auto-Reminders" iconPosition="start" />
            <Tab icon={<CampaignIcon />} label="Custom Outreach" iconPosition="start" />
          </Tabs>
        </Box>
        <CardContent>
          {tab === 0 && (
            <Box sx={{ py: 2 }}>
              <Typography variant="h6" gutterBottom>
                Automated Appointment Reminders
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                The AI will scan for appointments scheduled for tomorrow and call customers to confirm or reschedule.
              </Typography>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
                onClick={handleTriggerReminders}
                disabled={loading}
              >
                Scan & Trigger Now
              </Button>
            </Box>
          )}

          {tab === 1 && (
            <Box sx={{ py: 2 }}>
              <Typography variant="h6" gutterBottom>
                Targeted Outreach Campaign
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="AI Briefing"
                    placeholder="e.g., Call these customers to offer a 20% discount on their next service if they book today."
                    multiline
                    rows={3}
                    value={briefing}
                    onChange={(e) => setBriefing(e.target.value)}
                    helperText="What should the AI talk about during the call?"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Customer IDs (comma separated)"
                    placeholder="1, 2, 3..."
                    value={customerIds}
                    onChange={(e) => setCustomerIds(e.target.value)}
                    helperText="Specify which customers should receive this call."
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
                    onClick={handleTriggerCustom}
                    disabled={loading}
                  >
                    Start Outreach
                  </Button>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
}
