'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Typography, Box, Grid, Card, CardContent, CardHeader, FormControl, InputLabel, Select, MenuItem, LinearProgress, Tabs, Tab } from '@mui/material';
import api from '@/services/api'; // Use the centralized API service

// Simplified placeholder for the MetricCard to reduce complexity
function MetricCard({ title, value }: { title: string; value: string | number; }) {
  return (
    <Card><CardContent><Typography color="textSecondary">{title}</Typography><Typography variant="h4">{value}</Typography></CardContent></Card>
  );
}

function TabPanel(props: any) {
  const { children, value, index } = props;
  return value === index ? <Box sx={{ p: 3 }}>{children}</Box> : null;
}

export default function AnalyticsPage() {
  const [tabValue, setTabValue] = useState(0);
  const [timeframe, setTimeframe] = useState('30d');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Step 1: Get the business ID
    const fetchBusinessId = async () => {
      try {
        const res = await api.get('/businesses');
        if (res.data.length > 0) {
          setBusinessId(res.data[0].id);
        } else {
          setError('No business found. Please complete business setup.');
        }
      } catch (err) {
        console.error('Error fetching business ID:', err);
        setError('Could not fetch business data. You may need to log in again.');
        if ((err as any).response?.status === 401) {
            window.location.href = '/login';
        }
      }
    };
    fetchBusinessId();
  }, []);

  useEffect(() => {
    // Step 2: Fetch analytics data once businessId is available
    if (!businessId) return;
    
    const fetchAnalyticsData = async () => {
      setLoading(true);
      setError('');
      try {
        // Use the centralized api service with correct relative paths
        const [analyticsRes] = await Promise.all([
          api.get(`/analytics/business/${businessId}?timeframe=${timeframe}`),
        ]);
        setAnalyticsData(analyticsRes.data);
      } catch (err) {
        console.error('Error fetching analytics data:', err);
        setError('Failed to load analytics data.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, [businessId, timeframe]);

  if (error) return <Container sx={{ mt: 4 }}><Typography color="error">{error}</Typography></Container>;
  if (loading || !analyticsData) return <Container sx={{ mt: 4 }}><LinearProgress /></Container>;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">Analytics Dashboard</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} label="Time Range">
            <MenuItem value="7d">Last 7 days</MenuItem>
            <MenuItem value="30d">Last 30 days</MenuItem>
            <MenuItem value="90d">Last 90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="Overview" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}><MetricCard title="Total Calls" value={analyticsData.totalCalls || 0} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard title="Appointments Booked" value={analyticsData.appointmentsBooked || 0} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard title="Success Rate" value={`${analyticsData.successRate || 0}%`} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard title="Avg Call Duration" value={`${analyticsData.avgCallDuration || 0}s`} /></Grid>
        </Grid>
      </TabPanel>
    </Container>
  );
}
