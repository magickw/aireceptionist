'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import PhoneIcon from '@mui/icons-material/Phone';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import PeopleIcon from '@mui/icons-material/People';
import EventIcon from '@mui/icons-material/Event';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CallIcon from '@mui/icons-material/Call';
import LoginIcon from '@mui/icons-material/Login';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';

interface DashboardMetrics {
  totalCalls: number;
  autonomousResolutions: number;
  activeWorkflows: number;
  aiSuccessRate: number;
  avgResponseTime: number;
  avgCallDuration: number;
}

interface LiveCall {
  id: string;
  customerPhone: string;
  duration: number;
  status: 'active' | 'ringing' | 'on-hold';
  reasoning: string;
}

interface RecentActivity {
  id: string;
  type: 'call' | 'workflow' | 'automation';
  customer: string;
  time: string;
  status: 'success' | 'failed' | 'pending';
  description: string;
}

interface WorkflowExecution {
  id: string;
  task: string;
  status: string;
  desc: string;
  time: string;
}

export default function Dashboard() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalCalls: 0,
    autonomousResolutions: 0,
    activeWorkflows: 0,
    aiSuccessRate: 0,
    avgResponseTime: 0,
    avgCallDuration: 0,
  });
  const [liveCalls, setLiveCalls] = useState<LiveCall[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchDashboardData = async () => {
      try {
        // Fetch business data first
        const businessResponse = await api.get('/businesses');
        if (businessResponse.data.length > 0) {
          const bizId = businessResponse.data[0].id;
          setBusinessId(bizId);

          // Fetch all dashboard data in parallel
          const [analyticsResponse, realtimeResponse, callLogsResponse, appointmentsResponse, ordersResponse] =
            await Promise.all([
              api.get(`/analytics/business/${bizId}`),
              api.get(`/analytics/business/${bizId}/realtime`),
              api.get(`/call-logs/?business_id=${bizId}`),
              api.get(`/appointments/business/${bizId}`),
              api.get(`/orders/?business_id=${bizId}`),
            ]);

          const analyticsData = analyticsResponse.data;
          const realtimeData = realtimeResponse.data;
          const callLogs = callLogsResponse.data || [];
          const appointments = appointmentsResponse.data || [];
          const orders = ordersResponse.data || [];
          
          // Process metrics from real data
          const totalCalls = analyticsData.totalCalls || realtimeData.todayStats?.calls_today || 0;
          const completedCalls = realtimeData.todayStats?.completed_calls || 0;
          const successRate = totalCalls > 0 ? (completedCalls / totalCalls * 100) : 0;
          
          setMetrics({
            totalCalls: totalCalls,
            autonomousResolutions: appointments.length + orders.length,
            activeWorkflows: realtimeData.activeCalls || 0,
            aiSuccessRate: Math.round(analyticsData.successRate || successRate * 10) / 10,
            avgResponseTime: 0.8, // Would need to track this separately
            avgCallDuration: analyticsData.avgCallDuration || realtimeData.todayStats?.avg_duration_today || 0,
          });
          
          // Process live calls from realtime data
          const activeCalls: LiveCall[] = (realtimeData.recentCalls || [])
            .filter((call: any) => call.status === 'active')
            .map((call: any) => ({
              id: call.id,
              customerPhone: call.customer_phone || 'Unknown',
              duration: call.duration_seconds || 0,
              status: 'active',
              reasoning: call.sentiment ? `Sentiment: ${call.sentiment}` : 'In progress',
            }));
          setLiveCalls(activeCalls);
          
          // Process recent activity from call logs
          const activities: RecentActivity[] = [
            ...callLogs.slice(0, 5).map((log: any) => ({
              id: log.id,
              type: 'call' as const,
              customer: log.customer_phone || 'Unknown',
              time: log.started_at || log.created_at,
              status: log.status === 'ended' ? 'success' as const : 'pending' as const,
              description: `Call ${log.status || 'completed'} - ${log.duration_seconds || 0}s`,
            })),
            ...appointments.slice(0, 3).map((apt: any) => ({
              id: `apt-${apt.id}`,
              type: 'workflow' as const,
              customer: apt.customer_name || 'Unknown',
              time: apt.created_at,
              status: 'success' as const,
              description: `Appointment booked for ${apt.service_type || 'service'}`,
            })),
          ];
          
          // Sort by time and take top 5
          activities.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
          setRecentActivity(activities.slice(0, 5));
          
          // Process workflow-like activities from orders and appointments
          const workflowList: WorkflowExecution[] = [
            ...orders.slice(0, 3).map((order: any) => ({
              id: `order-${order.id}`,
              task: 'Order Placed',
              status: order.status?.toUpperCase() || 'PENDING',
              desc: `${order.customer_name || 'Customer'} ordered - Total: $${order.total_amount || 0}`,
              time: formatTimeAgo(order.created_at),
            })),
            ...appointments.slice(0, 3).map((apt: any) => ({
              id: `apt-${apt.id}`,
              task: 'Appointment Booked',
              status: apt.status?.toUpperCase() || 'SCHEDULED',
              desc: `${apt.customer_name || 'Customer'} - ${apt.service_type || 'Service'}`,
              time: formatTimeAgo(apt.created_at),
            })),
          ];
          setWorkflows(workflowList.slice(0, 4));
        }
        
        // Reset error count on successful fetch
        setConsecutiveErrors(0);
        setError('');
        
      } catch (error: any) {
        console.error('Error fetching dashboard data:', error);
        setConsecutiveErrors(prev => prev + 1);
        
        // Stop showing error after first occurrence to avoid console spam
        if (consecutiveErrors === 0) {
          setError(error?.response?.data?.detail || error?.message || 'Failed to fetch dashboard data');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
    
    // Set up real-time updates (every 30 seconds)
    // Stop polling if there are too many consecutive errors
    let interval: NodeJS.Timeout;
    if (consecutiveErrors < 5) {
      interval = setInterval(fetchDashboardData, 30000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAuthenticated, consecutiveErrors]);

  const formatTimeAgo = (dateStr: string): string => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'Just now';
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'success':
      case 'confirmed':
      case 'completed':
      case 'scheduled':
        return 'success';
      case 'pending':
      case 'ringing':
        return 'warning';
      case 'on-hold':
        return 'info';
      case 'failed':
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  if (isLoading && isAuthenticated) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ width: '100%' }}>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 }, px: { xs: 2, sm: 3 } }}>
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setError('')}>
          <Typography variant="body2">{error}</Typography>
          {consecutiveErrors >= 5 && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Auto-refresh has been paused due to connection issues. Please refresh the page.
            </Typography>
          )}
        </Alert>
      )}
      
      <Box sx={{ mb: { xs: 2, sm: 4 } }}>
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom 
          sx={{ 
            fontWeight: 'bold', 
            color: 'primary.main',
            fontSize: { xs: '1.75rem', sm: '2.125rem' }
          }}
        >
          Nova Agent Command Center
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          Real-time orchestration of speech-to-speech reasoning and UI automation
        </Typography>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 'bold' }}>Total Traffic</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1 }}>{metrics.totalCalls}</Typography>
              <Typography variant="body2" color="text.secondary">All time calls</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #10b981' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 'bold' }}>Autonomous Resolutions</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1, color: 'success.main' }}>{metrics.autonomousResolutions}</Typography>
              <Typography variant="body2" color="text.secondary">Appointments & Orders</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 'bold' }}>Active Calls</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1, color: 'primary.main' }}>{metrics.activeWorkflows}</Typography>
              <Typography variant="body2" color="text.secondary">Currently in progress</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 'bold' }}>Avg Call Duration</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1 }}>{Math.floor(metrics.avgCallDuration / 60)}:{(metrics.avgCallDuration % 60).toString().padStart(2, '0')}</Typography>
              <Typography variant="body2" color="info.main">Minutes:Seconds</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 'bold' }}>AI Success Rate</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1, color: 'secondary.main' }}>{metrics.aiSuccessRate}%</Typography>
              <LinearProgress variant="determinate" value={metrics.aiSuccessRate} color="secondary" sx={{ mt: 1 }} />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 'bold' }}>System Status</Typography>
              <Box sx={{ mt: 1 }}>
                <Chip label="SONIC: ONLINE" size="small" color="success" sx={{ mb: 0.5, fontSize: '0.6rem', width: '100%' }} />
                <Chip label="LITE: ONLINE" size="small" color="success" sx={{ mb: 0.5, fontSize: '0.6rem', width: '100%' }} />
                <Chip label="ACT: ACTIVE" size="small" color="info" sx={{ fontSize: '0.6rem', width: '100%' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Live Orchestration */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                {liveCalls.length > 0 && <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />}
                Live Agent Orchestration
              </Typography>
              {liveCalls.length > 0 ? (
                <List>
                  {liveCalls.map((call) => (
                    <ListItem key={call.id} divider sx={{ px: 0 }}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main' }}><CallIcon /></Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={call.customerPhone} 
                        secondary={<span className="font-mono text-xs">{call.reasoning}</span>} 
                      />
                      <Chip label={call.status.toUpperCase()} size="small" color="success" />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '250px', color: 'text.secondary' }}>
                  <PhoneIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="body1">No active calls</Typography>
                  <Typography variant="body2">Calls will appear here in real-time</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Autonomous Workflows */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                Recent Activity
              </Typography>
              {workflows.length > 0 ? (
                <List>
                  {workflows.map((wf) => (
                    <ListItem key={wf.id} divider sx={{ px: 0 }}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'success.light' }}><SmartToyIcon /></Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={wf.task} 
                        secondary={`${wf.desc} • ${wf.time}`} 
                      />
                      <Chip label={wf.status} size="small" variant="outlined" color={getStatusColor(wf.status) as any} />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '250px', color: 'text.secondary' }}>
                  <SmartToyIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="body1">No recent activity</Typography>
                  <Typography variant="body2">Orders and appointments will appear here</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}