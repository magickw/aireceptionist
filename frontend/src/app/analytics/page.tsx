'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardHeader,
  FormControl, InputLabel, Select, MenuItem, LinearProgress, Tabs, Tab,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Button, ToggleButton, ToggleButtonGroup, Avatar, List, ListItem, ListItemAvatar, ListItemText
} from '@mui/material';
import { TrendingUp, Phone, CalendarMonth, People, SentimentSatisfied, SentimentDissatisfied, Download } from '@mui/icons-material';
import api, { reportsApi, sentimentApi, forecastingApi } from '@/services/api';

function TabPanel(props: any) {
  const { children, value, index } = props;
  return value === index ? <Box sx={{ p: 3 }}>{children}</Box> : null;
}

function MetricCard({ title, value, subtitle, trend, icon }: { title: string; value: string | number; subtitle?: string; trend?: number; icon?: React.ReactNode }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="textSecondary" variant="body2">{title}</Typography>
            <Typography variant="h4" sx={{ my: 1 }}>{value}</Typography>
            {subtitle && <Typography variant="caption" color="textSecondary">{subtitle}</Typography>}
            {trend !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                <TrendingUp fontSize="small" color={trend >= 0 ? 'success' : 'error'} />
                <Typography variant="body2" color={trend >= 0 ? 'success.main' : 'error.main'}>
                  {trend >= 0 ? '+' : ''}{trend}% vs last period
                </Typography>
              </Box>
            )}
          </Box>
          {icon && <Avatar sx={{ bgcolor: 'primary.light' }}>{icon}</Avatar>}
        </Box>
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const [tabValue, setTabValue] = useState(0);
  const [timeframe, setTimeframe] = useState('30d');
  const [view, setView] = useState('overview');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [reportData, setReportData] = useState<any>(null);
  const [sentimentData, setSentimentData] = useState<any>(null);
  const [forecastData, setForecastData] = useState<any>(null);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBusinessId = async () => {
      try {
        const res = await api.get('/businesses');
        if (res.data.length > 0) {
          setBusinessId(res.data[0].id);
        }
      } catch (err) {
        console.error('Error fetching business ID:', err);
      }
    };
    fetchBusinessId();
  }, []);

  useEffect(() => {
    if (!businessId) return;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const [analyticsRes, reportRes, sentimentRes, forecastRes] = await Promise.all([
          api.get(`/analytics/business/${businessId}?timeframe=${timeframe}`),
          reportsApi.generateReport(timeframe === '7d' ? 'weekly' : timeframe === '30d' ? 'weekly' : 'monthly'),
          sentimentApi.getBusiness(timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : 90),
          forecastingApi.getPredictions(7)
        ]);
        setAnalyticsData(analyticsRes.data);
        setReportData(reportRes.data);
        setSentimentData(sentimentRes.data);
        setForecastData(forecastRes.data);
      } catch (err) {
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [businessId, timeframe]);

  const handleExport = async () => {
    try {
      const res = await reportsApi.exportCSV();
      const blob = new Blob([res.data.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = res.data.filename;
      a.click();
    } catch (err) { console.error('Export failed:', err); }
  };

  if (loading || !analyticsData) return <Container sx={{ mt: 4 }}><LinearProgress /></Container>;

  const totalCalls = reportData?.call_metrics?.total_calls || analyticsData?.totalCalls || 0;
  const completedCalls = reportData?.call_metrics?.completed_calls || 0;
  const missedCalls = reportData?.call_metrics?.missed_calls || 0;
  const completionRate = reportData?.call_metrics?.completion_rate || analyticsData?.successRate || 0;
  const avgDuration = reportData?.call_metrics?.average_duration_seconds || analyticsData?.avgCallDuration || 0;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">Analytics Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <ToggleButtonGroup value={view} exclusive onChange={(_, v) => v && setView(v)} size="small">
            <ToggleButton value="overview">Overview</ToggleButton>
            <ToggleButton value="detailed">Detailed</ToggleButton>
          </ToggleButtonGroup>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} label="Time Range">
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <Button variant="outlined" startIcon={<Download />} onClick={handleExport}>
            Export
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Total Calls" value={totalCalls} subtitle="in this period" icon={<Phone />} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Completed" value={completedCalls} subtitle={`${completionRate}% success rate`} trend={5} icon={<SentimentSatisfied color="success" />} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Missed Calls" value={missedCalls} subtitle="needs attention" trend={-8} icon={<SentimentDissatisfied color="error" />} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Avg Duration" value={`${Math.round(avgDuration)}s`} subtitle="per call" icon={<CalendarMonth />} />
        </Grid>
      </Grid>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
        <Tab label="Overview" />
        <Tab label="Sentiment" />
        <Tab label="Forecasting" />
        <Tab label="Customers" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title="Call Volume Trend" />
              <CardContent>
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography color="textSecondary">Call volume chart visualization</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardHeader title="Quick Stats" />
              <CardContent>
                <List>
                  <ListItem>
                    <ListItemAvatar><Avatar sx={{ bgcolor: 'primary.main' }}><Phone /></Avatar></ListItemAvatar>
                    <ListItemText primary="Peak Hours" secondary="9 AM - 11 AM" />
                  </ListItem>
                  <ListItem>
                    <ListItemAvatar><Avatar sx={{ bgcolor: 'success.main' }}><CalendarMonth /></Avatar></ListItemAvatar>
                    <ListItemText primary="Appointments" secondary={`${analyticsData?.appointmentsBooked || 0} booked`} />
                  </ListItem>
                  <ListItem>
                    <ListItemAvatar><Avatar sx={{ bgcolor: 'info.main' }}><People /></Avatar></ListItemAvatar>
                    <ListItemText primary="Unique Callers" secondary={`${reportData?.customer_metrics?.unique_customers || 0} callers`} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h2" color="success.main">{sentimentData?.sentiment_distribution?.positive?.percentage || 0}%</Typography>
                <Typography>Positive</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h2">{sentimentData?.sentiment_distribution?.neutral?.percentage || 0}%</Typography>
                <Typography>Neutral</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h2" color="error.main">{sentimentData?.sentiment_distribution?.negative?.percentage || 0}%</Typography>
                <Typography>Negative</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Card>
          <CardHeader title="7-Day Call Volume Forecast" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Day</TableCell>
                    <TableCell>Predicted Calls</TableCell>
                    <TableCell>Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {forecastData?.predictions?.map((pred: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell>{pred.date}</TableCell>
                      <TableCell>{pred.day_of_week}</TableCell>
                      <TableCell><Typography variant="h6">{pred.predicted_calls}</Typography></TableCell>
                      <TableCell>
                        <Chip label={pred.confidence} size="small" 
                          color={pred.confidence === 'high' ? 'success' : pred.confidence === 'medium' ? 'warning' : 'default'} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Customer Metrics" />
              <CardContent>
                <Box sx={{ mb: 2 }}><Typography variant="body2">Unique Customers</Typography><Typography variant="h5">{reportData?.customer_metrics?.unique_customers || 0}</Typography></Box>
                <Box sx={{ mb: 2 }}><Typography variant="body2">New Customers</Typography><Typography variant="h5" color="success.main">{reportData?.customer_metrics?.new_customers || 0}</Typography></Box>
                <Box><Typography variant="body2">Returning Customers</Typography><Typography variant="h5" color="info.main">{reportData?.customer_metrics?.returning_customers || 0}</Typography></Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Hourly Distribution" />
              <CardContent>
                <Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography color="textSecondary">Hourly distribution chart</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Container>
  );
}
