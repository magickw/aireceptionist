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
import { useTheme, alpha } from '@mui/material/styles';
import PhoneIcon from '@mui/icons-material/Phone';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import PeopleIcon from '@mui/icons-material/People';
import EventIcon from '@mui/icons-material/Event';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CallIcon from '@mui/icons-material/Call';
import LoginIcon from '@mui/icons-material/Login';
import SpeedIcon from '@mui/icons-material/Speed';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import SavingsIcon from '@mui/icons-material/Savings';
import { MetricCard } from '@/components/ui/MetricCard';
import { EmptyState } from '@/components/ui/EmptyState';
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

interface ROIMetrics {
  human_hours_saved: number;
  cost_savings: number;
  revenue_captured: number;
  appointment_opportunity: number;
  total_value_generated: number;
}

export default function Dashboard() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const theme = useTheme();
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalCalls: 0,
    autonomousResolutions: 0,
    activeWorkflows: 0,
    aiSuccessRate: 0,
    avgResponseTime: 0,
    avgCallDuration: 0,
  });
  const [roi, setRoi] = useState<ROIMetrics>({
    human_hours_saved: 0,
    cost_savings: 0,
    revenue_captured: 0,
    appointment_opportunity: 0,
    total_value_generated: 0,
  });
  const [liveCalls, setLiveCalls] = useState<LiveCall[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchDashboardData = async () => {
      try {
        // Fetch business data first
        const businessResponse = await api.get('/businesses');
        if (businessResponse.data.length > 0) {
          const bizId = businessResponse.data[0].id;
          setBusinessId(bizId);

          // Fetch all dashboard data in parallel — use allSettled so one failure doesn't kill the whole dashboard
          const [analyticsResult, realtimeResult, callLogsResult, appointmentsResult, ordersResult, roiResult] =
            await Promise.allSettled([
              api.get(`/analytics/business/${bizId}`),
              api.get(`/analytics/business/${bizId}/realtime`),
              api.get(`/call-logs/?business_id=${bizId}`),
              api.get(`/appointments/business/${bizId}`),
              api.get(`/orders/?business_id=${bizId}`),
              api.get(`/analytics/roi?business_id=${bizId}`),
            ]);

          const analyticsData = analyticsResult.status === 'fulfilled' ? analyticsResult.value.data : {};
          const realtimeData = realtimeResult.status === 'fulfilled' ? realtimeResult.value.data : {};
          const callLogs = callLogsResult.status === 'fulfilled' ? (callLogsResult.value.data || []) : [];
          const appointments = appointmentsResult.status === 'fulfilled' ? (appointmentsResult.value.data || []) : [];
          const orders = ordersResult.status === 'fulfilled' ? (ordersResult.value.data || []) : [];
          const roiData = roiResult.status === 'fulfilled' ? roiResult.value.data : null;

          if (roiData) {
            setRoi(roiData);
          }

          // Log individual failures for debugging without crashing the dashboard
          const results = [analyticsResult, realtimeResult, callLogsResult, appointmentsResult, ordersResult, roiResult];
          const names = ['analytics', 'realtime', 'call-logs', 'appointments', 'orders', 'roi'];
          results.forEach((r, i) => {
            if (r.status === 'rejected') console.warn(`Dashboard: ${names[i]} failed:`, r.reason?.message);
          });
          
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
        
        // Reset error on successful fetch
        setError('');
        
      } catch (error: any) {
        console.error('Error fetching dashboard data:', error);
        setError(error?.response?.data?.detail || error?.message || 'Failed to fetch dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();

    // Set up real-time updates (every 30 seconds)
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

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
        </Alert>
      )}

      <Box sx={{ mb: { xs: 3, sm: 5 } }}>
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          sx={{
            fontWeight: 800,
            color: 'text.primary',
            fontSize: { xs: '1.75rem', sm: '2.125rem', md: '2.5rem' },
          }}
        >
          Nova Agent Command Center
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' }, maxWidth: 600 }}>
          Real-time orchestration of speech-to-speech reasoning and UI automation
        </Typography>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 4, sm: 5 } }}>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Total Traffic"
            value={metrics.totalCalls}
            icon={<PhoneIcon />}
            color="primary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Autonomous Resolutions"
            value={metrics.autonomousResolutions}
            icon={<CheckCircleIcon />}
            color="success"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Active Calls"
            value={metrics.activeWorkflows}
            icon={<CallIcon />}
            color="info"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Avg Duration"
            value={`${Math.floor(metrics.avgCallDuration / 60)}:${(metrics.avgCallDuration % 60).toString().padStart(2, '0')}`}
            icon={<AccessTimeIcon />}
            color="secondary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="AI Success Rate"
            value={`${metrics.aiSuccessRate}%`}
            icon={<TrendingUpIcon />}
            color="success"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                System Status
              </Typography>
              <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'success.main' }} />
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>SONIC: ONLINE</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'success.main' }} />
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>LITE: ONLINE</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'info.main' }} />
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>ACT: ACTIVE</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ROI Insights */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
          Autonomous ROI Insights
        </Typography>
        <Grid container spacing={3} sx={{ mb: 5 }}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Human Hours Saved"
              value={`${roi.human_hours_saved} hrs`}
              icon={<AccessTimeIcon />}
              color="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Operational Savings"
              value={`$${roi.cost_savings}`}
              icon={<SavingsIcon />}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Revenue Captured"
              value={`$${roi.revenue_captured}`}
              icon={<MonetizationOnIcon />}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Value Generated"
              value={`$${roi.total_value_generated}`}
              icon={<TrendingUpIcon />}
              color="warning"
            />
          </Grid>
        </Grid>
      </Box>

      <Grid container spacing={3}>
        {/* Live Orchestration */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '450px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, overflow: 'auto', pt: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Live Agent Orchestration
                </Typography>
                {liveCalls.length > 0 && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: 'error.main',
                        animation: 'pulse 1.5s ease-in-out infinite',
                      }}
                    />
                    <Typography variant="caption" color="error.main" fontWeight={600}>
                      LIVE
                    </Typography>
                  </Box>
                )}
              </Box>
              {liveCalls.length > 0 ? (
                <List>
                  {liveCalls.map((call) => (
                    <ListItem
                      key={call.id}
                      divider
                      sx={{
                        px: 0,
                        py: 2,
                        borderRadius: 2,
                        '&:hover': {
                          bgcolor: alpha(theme.palette.primary.main, 0.04),
                        },
                      }}
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>
                          <CallIcon fontSize="small" />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={call.customerPhone}
                        secondary={
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {call.reasoning}
                          </Typography>
                        }
                        primaryTypographyProps={{ fontWeight: 600 }}
                      />
                      <Chip
                        label={call.status.toUpperCase()}
                        size="small"
                        color="success"
                        sx={{ fontWeight: 600, borderRadius: 8 }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <EmptyState
                  icon={<PhoneIcon />}
                  title="No active calls"
                  description="Calls will appear here in real-time"
                  variant="default"
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Autonomous Workflows */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '450px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, overflow: 'auto', pt: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                Recent Activity
              </Typography>
              {workflows.length > 0 ? (
                <List>
                  {workflows.map((wf) => (
                    <ListItem
                      key={wf.id}
                      divider
                      sx={{
                        px: 0,
                        py: 2,
                        borderRadius: 2,
                        '&:hover': {
                          bgcolor: alpha(theme.palette.success.main, 0.04),
                        },
                      }}
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'success.light', width: 40, height: 40 }}>
                          <SmartToyIcon fontSize="small" />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={wf.task}
                        secondary={`${wf.desc} • ${wf.time}`}
                        primaryTypographyProps={{ fontWeight: 600 }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                      <Chip
                        label={wf.status}
                        size="small"
                        variant="outlined"
                        color={getStatusColor(wf.status) as any}
                        sx={{ fontWeight: 600, borderRadius: 8 }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <EmptyState
                  icon={<SmartToyIcon />}
                  title="No recent activity"
                  description="Orders and appointments will appear here"
                  variant="no-data"
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}