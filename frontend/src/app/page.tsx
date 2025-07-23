'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
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
import PhoneIcon from '@mui/icons-material/Phone';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import PeopleIcon from '@mui/icons-material/People';
import EventIcon from '@mui/icons-material/Event';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CallIcon from '@mui/icons-material/Call';
import axios from 'axios';

interface DashboardMetrics {
  totalCalls: number;
  appointmentsBooked: number;
  activeCustomers: number;
  aiResponseRate: number;
  callsToday: number;
  avgCallDuration: number;
}

interface LiveCall {
  id: string;
  customerPhone: string;
  duration: number;
  status: 'active' | 'ringing' | 'on-hold';
  aiHandling: boolean;
}

interface RecentActivity {
  id: string;
  type: 'call' | 'appointment' | 'message';
  customer: string;
  time: string;
  description: string;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalCalls: 0,
    appointmentsBooked: 0,
    activeCustomers: 0,
    aiResponseRate: 0,
    callsToday: 0,
    avgCallDuration: 0,
  });
  const [liveCalls, setLiveCalls] = useState<LiveCall[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch business data first
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const businessId = businessResponse.data[0].id;
          
          // Fetch analytics data
          const analyticsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics/business/${businessId}`);
          const analyticsData = analyticsResponse.data;
          
          // Fetch call logs for recent activity
          const callLogsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/call-logs/business/${businessId}`);
          const callLogs = callLogsResponse.data;
          
          // Fetch appointments
          const appointmentsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/appointments/business/${businessId}`);
          const appointments = appointmentsResponse.data;
          
          // Process metrics
          setMetrics({
            totalCalls: analyticsData.totalCalls || 0,
            appointmentsBooked: appointments.length || 0,
            activeCustomers: new Set(callLogs.map((log: any) => log.customer_phone)).size,
            aiResponseRate: 95.2, // Mock data
            callsToday: callLogs.filter((log: any) => 
              new Date(log.created_at).toDateString() === new Date().toDateString()
            ).length,
            avgCallDuration: analyticsData.avgCallDuration || 0,
          });
          
          // Process recent activity
          const activities: RecentActivity[] = [
            ...callLogs.slice(0, 3).map((log: any) => ({
              id: log.id,
              type: 'call' as const,
              customer: log.customer_phone,
              time: new Date(log.created_at).toLocaleTimeString(),
              description: 'Incoming call handled by AI',
            })),
            ...appointments.slice(0, 2).map((apt: any) => ({
              id: apt.id,
              type: 'appointment' as const,
              customer: apt.customer_name,
              time: new Date(apt.created_at).toLocaleTimeString(),
              description: `Appointment booked for ${apt.service_type}`,
            })),
          ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 5);
          
          setRecentActivity(activities);
        }
        
        // Mock live calls data (in real app, this would be from WebSocket or real-time API)
        setLiveCalls([
          {
            id: '1',
            customerPhone: '+1 (555) 123-4567',
            duration: 127,
            status: 'active',
            aiHandling: true,
          },
          {
            id: '2',
            customerPhone: '+1 (555) 987-6543',
            duration: 45,
            status: 'on-hold',
            aiHandling: false,
          },
        ]);
        
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
    
    // Set up real-time updates (every 30 seconds)
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'ringing': return 'warning';
      case 'on-hold': return 'info';
      default: return 'default';
    }
  };

  if (isLoading) {
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
          Dashboard Overview
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          Real-time insights into your AI receptionist performance
        </Typography>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
        <Grid item xs={6} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 2 }, '&:last-child': { pb: { xs: 2, sm: 2 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flexDirection: { xs: 'column', sm: 'row' }, textAlign: { xs: 'center', sm: 'left' } }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: { xs: 0, sm: 2 }, mb: { xs: 1, sm: 0 }, width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                  <PhoneIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                    {metrics.totalCalls}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Total Calls
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={6} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 2 }, '&:last-child': { pb: { xs: 2, sm: 2 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flexDirection: { xs: 'column', sm: 'row' }, textAlign: { xs: 'center', sm: 'left' } }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: { xs: 0, sm: 2 }, mb: { xs: 1, sm: 0 }, width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                  <EventIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                    {metrics.appointmentsBooked}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Appointments
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 2 }, '&:last-child': { pb: { xs: 2, sm: 2 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flexDirection: { xs: 'column', sm: 'row' }, textAlign: { xs: 'center', sm: 'left' } }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: { xs: 0, sm: 2 }, mb: { xs: 1, sm: 0 }, width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                  <PeopleIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                    {metrics.activeCustomers}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Customers
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 2 }, '&:last-child': { pb: { xs: 2, sm: 2 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flexDirection: { xs: 'column', sm: 'row' }, textAlign: { xs: 'center', sm: 'left' } }}>
                <Avatar sx={{ bgcolor: 'secondary.main', color: 'primary.main', mr: { xs: 0, sm: 2 }, mb: { xs: 1, sm: 0 }, width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                  <SmartToyIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                    {metrics.aiResponseRate}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    AI Success
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 2 }, '&:last-child': { pb: { xs: 2, sm: 2 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flexDirection: { xs: 'column', sm: 'row' }, textAlign: { xs: 'center', sm: 'left' } }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: { xs: 0, sm: 2 }, mb: { xs: 1, sm: 0 }, width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                  <TrendingUpIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                    {metrics.callsToday}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Today
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <CallIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div">
                    {Math.round(metrics.avgCallDuration)}s
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Duration
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Live Calls */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '400px' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                Live Calls
              </Typography>
              {liveCalls.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    No active calls
                  </Typography>
                </Box>
              ) : (
                <List>
                  {liveCalls.map((call) => (
                    <ListItem key={call.id} divider>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: getStatusColor(call.status) + '.main' }}>
                          <PhoneIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={call.customerPhone}
                        secondary={`${call.status.toUpperCase()} • ${formatDuration(call.duration)}${call.aiHandling ? ' • AI HANDLING' : ''}`}
                      />
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={call.status.toUpperCase()}
                          color={getStatusColor(call.status) as any}
                          size="small"
                        />
                        {call.aiHandling && (
                          <Chip
                            label="AI HANDLING"
                            color="primary"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '400px' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                Recent Activity
              </Typography>
              {recentActivity.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    No recent activity
                  </Typography>
                </Box>
              ) : (
                <List>
                  {recentActivity.map((activity) => (
                    <ListItem key={activity.id} divider>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: activity.type === 'call' ? 'primary.main' : 'success.main' }}>
                          {activity.type === 'call' ? <PhoneIcon /> : <EventIcon />}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={activity.customer}
                        secondary={`${activity.description} • ${activity.time}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

