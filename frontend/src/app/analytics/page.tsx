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
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import LinearProgress from '@mui/material/LinearProgress';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import CallIcon from '@mui/icons-material/Call';
import EventIcon from '@mui/icons-material/Event';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PsychologyIcon from '@mui/icons-material/Psychology';
import axios from 'axios';

interface AnalyticsData {
  totalCalls: number;
  avgCallDuration: number;
  appointmentsBooked: number;
  successRate: number;
  dailyTrends: Array<{
    date: string;
    calls: number;
    avg_duration: number;
    avg_confidence: number;
  }>;
  intentAnalysis: Array<{
    intent: string;
    count: number;
    avg_confidence: number;
  }>;
  peakHours: Array<{
    hour: number;
    calls: number;
  }>;
  timeframe: string;
}

interface RevenueData {
  totalRevenue: number;
  avgAppointmentValue: number;
  appointmentRevenue: Array<{
    date: string;
    total_appointments: number;
  }>;
  timeframe: string;
}

interface RealtimeData {
  activeCalls: number;
  todayStats: {
    calls_today: number;
    avg_duration_today: number;
    completed_calls: number;
  };
  recentCalls: Array<{
    id: string;
    customer_phone: string;
    status: string;
    started_at: string;
    duration_seconds: number;
    ai_confidence: number;
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

function MetricCard({ title, value, icon, subtitle, color = 'primary' }: {
  title: string;
  value: string | number;
  icon: React.ReactElement;
  subtitle?: string;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
}) {
  return (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="h2" color={`${color}.main`}>
              {value}
            </Typography>
            {subtitle && (
              <Typography color="textSecondary" variant="body2">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar sx={{ bgcolor: `${color}.main`, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const [tabValue, setTabValue] = useState(0);
  const [timeframe, setTimeframe] = useState('30d');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueData | null>(null);
  const [realtimeData, setRealtimeData] = useState<RealtimeData | null>(null);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

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
    
    const fetchAnalyticsData = async () => {
      try {
        setLoading(true);
        const [analyticsResponse, revenueResponse, realtimeResponse] = await Promise.all([
          axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics/business/${businessId}?timeframe=${timeframe}`),
          axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics/business/${businessId}/revenue?timeframe=${timeframe}`),
          axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics/business/${businessId}/realtime`)
        ]);
        
        setAnalyticsData(analyticsResponse.data);
        setRevenueData(revenueResponse.data);
        setRealtimeData(realtimeResponse.data);
      } catch (error) {
        console.error('Error fetching analytics data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
    
    // Set up real-time updates
    const interval = setInterval(fetchAnalyticsData, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, [businessId, timeframe]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatPhone = (phone: string) => {
    return phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Analytics Dashboard
        </Typography>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor your AI receptionist performance and business insights
          </Typography>
        </Box>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            label="Time Range"
          >
            <MenuItem value="7d">Last 7 days</MenuItem>
            <MenuItem value="30d">Last 30 days</MenuItem>
            <MenuItem value="90d">Last 90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Overview" />
        <Tab label="Call Analytics" />
        <Tab label="Revenue" />
        <Tab label="Customer Intelligence" />
        <Tab label="Real-time" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* Overview Tab */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Calls"
              value={analyticsData?.totalCalls || 0}
              icon={<CallIcon />}
              subtitle={`Last ${timeframe.replace('d', ' days')}`}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Appointments Booked"
              value={analyticsData?.appointmentsBooked || 0}
              icon={<EventIcon />}
              subtitle="Confirmed bookings"
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Success Rate"
              value={`${analyticsData?.successRate || 0}%`}
              icon={<TrendingUpIcon />}
              subtitle="AI handled successfully"
              color="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Avg Call Duration"
              value={formatDuration(analyticsData?.avgCallDuration || 0)}
              icon={<AccessTimeIcon />}
              subtitle="Average per call"
              color="warning"
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'primary.main' }}><AnalyticsIcon /></Avatar>}
                title="Daily Call Trends"
                subheader="Call volume and performance over time"
              />
              <CardContent>
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography color="textSecondary">
                    Chart visualization will be implemented with a charting library
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'success.main' }}><PsychologyIcon /></Avatar>}
                title="Call Intents"
                subheader="Most common customer requests"
              />
              <CardContent>
                {analyticsData?.intentAnalysis.slice(0, 5).map((intent) => (
                  <Box key={intent.intent} sx={{ mb: 2 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                      <Typography variant="body2">
                        {intent.intent?.replace('_', ' ').toUpperCase() || 'Unknown'}
                      </Typography>
                      <Chip 
                        label={intent.count} 
                        size="small" 
                        color="primary"
                      />
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(intent.avg_confidence * 100) || 0}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Call Analytics Tab */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                title="Peak Call Hours"
                subheader="When customers call most frequently"
              />
              <CardContent>
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography color="textSecondary">
                    Hourly call distribution chart would be displayed here
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                title="Call Duration Distribution"
                subheader="How long calls typically last"
              />
              <CardContent>
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography color="textSecondary">
                    Duration distribution histogram would be displayed here
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Revenue Tab */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <MetricCard
              title="Total Revenue"
              value={`$${revenueData?.totalRevenue?.toLocaleString() || 0}`}
              icon={<AttachMoneyIcon />}
              subtitle={`Last ${timeframe.replace('d', ' days')}`}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <MetricCard
              title="Avg Appointment Value"
              value={`$${revenueData?.avgAppointmentValue || 0}`}
              icon={<TrendingUpIcon />}
              subtitle="Per appointment"
              color="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <MetricCard
              title="Conversion Rate"
              value={`${analyticsData && analyticsData.totalCalls > 0 
                ? Math.round((analyticsData.appointmentsBooked / analyticsData.totalCalls) * 100)
                : 0}%`}
              icon={<QueryStatsIcon />}
              subtitle="Calls to appointments"
              color="warning"
            />
          </Grid>
        </Grid>

        <Card>
          <CardHeader
            title="Revenue Trends"
            subheader="Revenue generated over time"
          />
          <CardContent>
            <Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography color="textSecondary">
                Revenue chart visualization would be displayed here
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* Customer Intelligence Tab */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'warning.main' }}><PsychologyIcon /></Avatar>}
                title="VIP Customers"
                subheader="High-value customers requiring special attention"
              />
              <CardContent>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Powered by Nova Multimodal Embeddings for customer intelligence
                </Alert>
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Chip label="PLATINUM" color="warning" variant="outlined" size="small" />
                  <Chip label="GOLD" color="warning" variant="outlined" size="small" />
                  <Chip label="SILVER" color="warning" variant="outlined" size="small" />
                  <Chip label="BRONZE" color="warning" variant="outlined" size="small" />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  VIP customers are identified based on satisfaction score, appointment frequency, and engagement level.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'error.main' }}><TrendingUpIcon /></Avatar>}
                title="Churn Risk Analysis"
                subheader="Customers at risk of leaving"
              />
              <CardContent>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Risk Levels</Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip label="HIGH" color="error" size="small" />
                    <Chip label="MEDIUM" color="warning" size="small" />
                    <Chip label="LOW" color="success" size="small" />
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Churn risk is calculated using sentiment analysis, complaint frequency, interaction patterns, and cancellation rates.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'info.main' }}><AnalyticsIcon /></Avatar>}
                title="Complaint Patterns"
                subheader="Common issues detected"
              />
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  Nova AI analyzes customer interactions to detect recurring complaint patterns and provides actionable recommendations for improvement.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                avatar={<Avatar sx={{ bgcolor: 'success.main' }}><EventIcon /></Avatar>}
                title="Semantic Search"
                subheader="Search customer history naturally"
              />
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  Use natural language to search across all customer interactions. Nova embeddings understand context and meaning beyond keywords.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        {/* Real-time Tab */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Active Calls"
              value={realtimeData?.activeCalls || 0}
              icon={<CallIcon />}
              subtitle="Currently in progress"
              color="error"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Today's Calls"
              value={realtimeData?.todayStats?.calls_today || 0}
              icon={<TrendingUpIcon />}
              subtitle="So far today"
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Completed Today"
              value={realtimeData?.todayStats?.completed_calls || 0}
              icon={<EventIcon />}
              subtitle="Successfully handled"
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Avg Duration Today"
              value={formatDuration(Math.round(realtimeData?.todayStats?.avg_duration_today || 0))}
              icon={<AccessTimeIcon />}
              subtitle="Today's average"
              color="info"
            />
          </Grid>
        </Grid>

        <Card>
          <CardHeader
            title="Recent Calls"
            subheader="Latest call activity"
            action={
              <Button variant="outlined" size="small">
                Refresh
              </Button>
            }
          />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Phone</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>AI Confidence</TableCell>
                    <TableCell>Started At</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {realtimeData?.recentCalls?.map((call) => (
                    <TableRow key={call.id}>
                      <TableCell>{formatPhone(call.customer_phone)}</TableCell>
                      <TableCell>
                        <Chip 
                          label={call.status}
                          color={call.status === 'ended' ? 'success' : call.status === 'active' ? 'warning' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{formatDuration(call.duration_seconds || 0)}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={(call.ai_confidence * 100) || 0}
                            sx={{ width: 50, height: 6 }}
                          />
                          <Typography variant="caption">
                            {Math.round((call.ai_confidence * 100) || 0)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {new Date(call.started_at).toLocaleTimeString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>
    </Container>
  );
}
