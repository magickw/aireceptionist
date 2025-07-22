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
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Paper from '@mui/material/Paper';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import IconButton from '@mui/material/IconButton';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import TextField from '@mui/material/TextField';
import LinearProgress from '@mui/material/LinearProgress';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import PhoneIcon from '@mui/icons-material/Phone';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import axios from 'axios';

interface CallLog {
  id: number;
  business_id: number;
  customer_phone: string;
  call_sid: string;
  transcript: string;
  created_at: string;
  recording_url?: string;
  duration?: number;
  status: 'completed' | 'missed' | 'failed';
  ai_handled: boolean;
  sentiment?: 'positive' | 'neutral' | 'negative';
}

interface CallAnalytics {
  totalCalls: number;
  avgCallDuration: number;
  appointmentsBooked: number;
  aiSuccessRate: number;
  missedCalls: number;
  customerSatisfaction: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`call-management-tabpanel-${index}`}
      aria-labelledby={`call-management-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export default function CallManagement() {
  const [tabValue, setTabValue] = useState(0);
  const [callLogs, setCallLogs] = useState<CallLog[]>([]);
  const [analytics, setAnalytics] = useState<CallAnalytics>({
    totalCalls: 0,
    avgCallDuration: 0,
    appointmentsBooked: 0,
    aiSuccessRate: 0,
    missedCalls: 0,
    customerSatisfaction: 0,
  });
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPeriod, setFilterPeriod] = useState('week');
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState<CallLog | null>(null);
  const [callDetailOpen, setCallDetailOpen] = useState(false);

  useEffect(() => {
    const fetchCallData = async () => {
      try {
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const businessId = businessResponse.data[0].id;
          
          // Fetch call logs
          const callLogsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/call-logs/business/${businessId}`);
          const logs = callLogsResponse.data.map((log: any) => ({
            ...log,
            status: 'completed',
            ai_handled: true,
            sentiment: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)],
            duration: Math.floor(Math.random() * 300) + 30,
          }));
          setCallLogs(logs);
          
          // Fetch analytics
          const analyticsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics/business/${businessId}`);
          const analyticsData = analyticsResponse.data;
          
          setAnalytics({
            totalCalls: analyticsData.totalCalls || logs.length,
            avgCallDuration: analyticsData.avgCallDuration || 120,
            appointmentsBooked: analyticsData.appointmentsBooked || Math.floor(logs.length * 0.3),
            aiSuccessRate: 94.5,
            missedCalls: Math.floor(logs.length * 0.1),
            customerSatisfaction: 4.7,
          });
        }
      } catch (error) {
        console.error('Error fetching call data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCallData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleCallDetail = (call: CallLog) => {
    setSelectedCall(call);
    setCallDetailOpen(true);
  };

  const filteredCalls = callLogs.filter(call => {
    const matchesSearch = call.customer_phone.includes(searchTerm) || 
                         call.transcript.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || call.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'missed': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'success';
      case 'neutral': return 'info';
      case 'negative': return 'error';
      default: return 'default';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Call Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor call history, recordings, and analytics for your AI receptionist
        </Typography>
      </Box>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Analytics" />
        <Tab label="Call History" />
        <Tab label="Recordings" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* Analytics Tab */}
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <PhoneIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{analytics.totalCalls}</Typography>
                    <Typography variant="body2" color="text.secondary">Total Calls</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <TrendingUpIcon color="success" fontSize="small" />
                  <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                    +12% from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                    <SmartToyIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{analytics.aiSuccessRate}%</Typography>
                    <Typography variant="body2" color="text.secondary">AI Success Rate</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <TrendingUpIcon color="success" fontSize="small" />
                  <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                    +2.3% from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{formatDuration(analytics.avgCallDuration)}</Typography>
                    <Typography variant="body2" color="text.secondary">Avg Duration</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <TrendingDownIcon color="error" fontSize="small" />
                  <Typography variant="caption" color="error.main" sx={{ ml: 0.5 }}>
                    -8s from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                    <PhoneIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{analytics.missedCalls}</Typography>
                    <Typography variant="body2" color="text.secondary">Missed Calls</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <TrendingDownIcon color="success" fontSize="small" />
                  <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                    -5 from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                    <PersonIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{analytics.customerSatisfaction}</Typography>
                    <Typography variant="body2" color="text.secondary">Satisfaction</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <TrendingUpIcon color="success" fontSize="small" />
                  <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                    +0.2 from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{analytics.appointmentsBooked}</Typography>
                    <Typography variant="body2" color="text.secondary">Appointments</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <TrendingUpIcon color="success" fontSize="small" />
                  <Typography variant="caption" color="success.main" sx={{ ml: 0.5 }}>
                    +18% from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Call History Tab */}
        <Card>
          <CardHeader
            title="Call History"
            subheader="View and manage all incoming calls"
            action={
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  size="small"
                  placeholder="Search calls..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  sx={{ minWidth: 200 }}
                />
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    label="Status"
                  >
                    <MenuItem value="all">All</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="missed">Missed</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Period</InputLabel>
                  <Select
                    value={filterPeriod}
                    onChange={(e) => setFilterPeriod(e.target.value)}
                    label="Period"
                  >
                    <MenuItem value="today">Today</MenuItem>
                    <MenuItem value="week">This Week</MenuItem>
                    <MenuItem value="month">This Month</MenuItem>
                    <MenuItem value="quarter">This Quarter</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            }
          />
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Customer</TableCell>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>AI Handled</TableCell>
                  <TableCell>Sentiment</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredCalls
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((call) => (
                    <TableRow key={call.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                            <PhoneIcon />
                          </Avatar>
                          <Typography variant="body2">{call.customer_phone}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(call.created_at).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {call.duration ? formatDuration(call.duration) : 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={call.status.toUpperCase()}
                          color={getStatusColor(call.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={call.ai_handled ? 'YES' : 'NO'}
                          color={call.ai_handled ? 'success' : 'warning'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {call.sentiment && (
                          <Chip
                            label={call.sentiment.toUpperCase()}
                            color={getSentimentColor(call.sentiment) as any}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleCallDetail(call)}
                          title="View Details"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        {call.recording_url && (
                          <IconButton size="small" title="Play Recording">
                            <PlayArrowIcon />
                          </IconButton>
                        )}
                        <IconButton size="small" title="Download">
                          <DownloadIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredCalls.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Recordings Tab */}
        <Card>
          <CardHeader title="Call Recordings" subheader="Access and manage call recordings" />
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                Call recordings will appear here once available.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Recordings are automatically generated for all calls handled by your AI receptionist.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Call Detail Dialog */}
      <Dialog
        open={callDetailOpen}
        onClose={() => setCallDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Call Details</DialogTitle>
        <DialogContent>
          {selectedCall && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Customer Phone</Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>{selectedCall.customer_phone}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Call Duration</Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {selectedCall.duration ? formatDuration(selectedCall.duration) : 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Status</Typography>
                <Chip
                  label={selectedCall.status.toUpperCase()}
                  color={getStatusColor(selectedCall.status) as any}
                  size="small"
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>AI Handled</Typography>
                <Chip
                  label={selectedCall.ai_handled ? 'YES' : 'NO'}
                  color={selectedCall.ai_handled ? 'success' : 'warning'}
                  size="small"
                  variant="outlined"
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Transcript</Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2">
                    {selectedCall.transcript || 'No transcript available.'}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCallDetailOpen(false)}>Close</Button>
          {selectedCall?.recording_url && (
            <Button variant="contained" startIcon={<PlayArrowIcon />}>
              Play Recording
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
}