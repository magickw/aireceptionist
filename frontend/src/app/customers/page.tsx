'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  TextField,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Avatar,
  Alert,
  CircularProgress,
  InputAdornment,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Search,
  Person,
  Phone,
  TrendingUp,
  TrendingDown,
  Warning,
  Star,
  Refresh,
  Call,
  CalendarMonth,
  OpenInNew,
  Close,
  SentimentSatisfied,
  SentimentNeutral,
  SentimentDissatisfied
} from '@mui/icons-material';
import api from '@/services/api';

interface Customer {
  phone: string;
  call_count: number;
  last_contact: string | null;
  avg_confidence: number;
  appointment_count: number;
  churn_risk: any;
  vip_status: any;
}

interface CustomerDetails {
  phone: string;
  calls: any[];
  appointments: any[];
  churn_risk: any;
  vip_status: any;
  stats: any;
}

interface Insights {
  total_customers: number;
  vip_count: number;
  high_risk_count: number;
  complaint_trends: any[];
  top_issues: any[];
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [tabValue, setTabValue] = useState(0);
  
  // Detail dialog
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerDetails | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCustomers, setTotalCustomers] = useState(0);

  useEffect(() => {
    fetchCustomers();
    fetchInsights();
  }, [page]);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const res = await api.get('/customer-intelligence/customers', {
        params: { page, page_size: 20, sort_by: 'last_contact' }
      });
      setCustomers(res.data.customers || []);
      setTotalPages(res.data.total_pages || 1);
      setTotalCustomers(res.data.total || 0);
    } catch (error) {
      console.error('Failed to fetch customers', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const res = await api.get('/customer-intelligence/insights');
      setInsights(res.data);
    } catch (error) {
      console.error('Failed to fetch insights', error);
    }
  };

  const fetchCustomerDetails = async (phone: string) => {
    try {
      setDetailLoading(true);
      const res = await api.get(`/customer-intelligence/customer/${phone}`);
      setSelectedCustomer(res.data);
    } catch (error) {
      console.error('Failed to fetch customer details', error);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCustomerClick = (customer: Customer) => {
    fetchCustomerDetails(customer.phone);
    setDetailDialogOpen(true);
  };

  const getChurnRiskColor = (risk: any) => {
    if (!risk) return 'default';
    switch (risk.risk_level) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getChurnRiskIcon = (risk: any) => {
    if (!risk) return <SentimentNeutral />;
    switch (risk.risk_level) {
      case 'high': return <SentimentDissatisfied />;
      case 'medium': return <SentimentNeutral />;
      case 'low': return <SentimentSatisfied />;
      default: return <SentimentNeutral />;
    }
  };

  const filteredCustomers = searchQuery
    ? customers.filter(c => c.phone.includes(searchQuery))
    : customers;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Customer Intelligence</Typography>
        <Button startIcon={<Refresh />} onClick={() => { fetchCustomers(); fetchInsights(); }}>
          Refresh
        </Button>
      </Box>

      {/* Insights Cards */}
      {insights && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <Person />
                </Avatar>
                <Box>
                  <Typography variant="h4">{insights.total_customers}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Customers</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', width: 56, height: 56 }}>
                  <Star />
                </Avatar>
                <Box>
                  <Typography variant="h4">{insights.vip_count}</Typography>
                  <Typography variant="body2" color="text.secondary">VIP Customers</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', width: 56, height: 56 }}>
                  <Warning />
                </Avatar>
                <Box>
                  <Typography variant="h4">{insights.high_risk_count}</Typography>
                  <Typography variant="body2" color="text.secondary">High Risk</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', width: 56, height: 56 }}>
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography variant="h5">{insights.top_issues?.[0]?.issue || 'N/A'}</Typography>
                  <Typography variant="body2" color="text.secondary">Top Issue</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Main Content */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label="All Customers" />
            <Tab label="VIP Customers" />
            <Tab label="At Risk" />
          </Tabs>
        </Box>
        
        <CardContent>
          {/* Search */}
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Search by phone number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          {loading ? (
            <LinearProgress />
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Customer</TableCell>
                      <TableCell align="center">Calls</TableCell>
                      <TableCell align="center">Appointments</TableCell>
                      <TableCell align="center">AI Confidence</TableCell>
                      <TableCell align="center">Last Contact</TableCell>
                      <TableCell align="center">Churn Risk</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredCustomers.map((customer) => (
                      <TableRow 
                        key={customer.phone} 
                        hover 
                        sx={{ cursor: 'pointer' }}
                        onClick={() => handleCustomerClick(customer)}
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Phone fontSize="small" color="action" />
                            {customer.phone}
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            icon={<Call />} 
                            label={customer.call_count} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            icon={<CalendarMonth />} 
                            label={customer.appointment_count} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography 
                            variant="body2" 
                            color={customer.avg_confidence > 0.8 ? 'success.main' : customer.avg_confidence > 0.6 ? 'warning.main' : 'error.main'}
                          >
                            {customer.avg_confidence ? `${(customer.avg_confidence * 100).toFixed(1)}%` : 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          {customer.last_contact 
                            ? new Date(customer.last_contact).toLocaleDateString() 
                            : 'Never'}
                        </TableCell>
                        <TableCell align="center">
                          {customer.churn_risk ? (
                            <Chip 
                              icon={getChurnRiskIcon(customer.churn_risk)}
                              label={customer.churn_risk.risk_level || 'Unknown'}
                              color={getChurnRiskColor(customer.churn_risk) as any}
                              size="small"
                            />
                          ) : (
                            <Chip label="Unknown" size="small" variant="outlined" />
                          )}
                        </TableCell>
                        <TableCell align="center">
                          {customer.vip_status ? (
                            <Chip 
                              icon={<Star />} 
                              label={customer.vip_status.tier || 'VIP'} 
                              color="warning" 
                              size="small"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">Regular</Typography>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleCustomerClick(customer); }}>
                            <OpenInNew />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              {/* Pagination */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Showing {filteredCustomers.length} of {totalCustomers} customers
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button 
                    disabled={page === 1}
                    onClick={() => setPage(p => p - 1)}
                  >
                    Previous
                  </Button>
                  <Button 
                    disabled={page >= totalPages}
                    onClick={() => setPage(p => p + 1)}
                  >
                    Next
                  </Button>
                </Box>
              </Box>
            </>
          )}
        </CardContent>
      </Card>

      {/* Customer Detail Dialog */}
      <Dialog 
        open={detailDialogOpen} 
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Phone />
            <Typography>{selectedCustomer?.phone}</Typography>
          </Box>
          <IconButton onClick={() => setDetailDialogOpen(false)}>
            <Close />
          </IconButton>
        </DialogTitle>
        
        <DialogContent>
          {detailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedCustomer ? (
            <Box>
              {/* Stats */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{selectedCustomer.stats.total_calls}</Typography>
                      <Typography variant="body2" color="text.secondary">Total Calls</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{selectedCustomer.stats.total_appointments}</Typography>
                      <Typography variant="body2" color="text.secondary">Appointments</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      {selectedCustomer.churn_risk ? (
                        <>
                          <Typography variant="h4" color={`${getChurnRiskColor(selectedCustomer.churn_risk)}.main`}>
                            {Math.round(selectedCustomer.churn_risk.risk_score * 100)}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary">Churn Risk</Typography>
                        </>
                      ) : (
                        <>
                          <Typography variant="h4">N/A</Typography>
                          <Typography variant="body2" color="text.secondary">Churn Risk</Typography>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      {selectedCustomer.vip_status ? (
                        <>
                          <Typography variant="h4" color="warning.main">
                            <Star />
                          </Typography>
                          <Typography variant="body2" color="text.secondary">{selectedCustomer.vip_status.tier}</Typography>
                        </>
                      ) : (
                        <>
                          <Typography variant="h4">Regular</Typography>
                          <Typography variant="body2" color="text.secondary">Status</Typography>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Churn Risk Details */}
              {selectedCustomer.churn_risk && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>Churn Risk Analysis</Typography>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Risk Level: <Chip 
                          label={selectedCustomer.churn_risk.risk_level} 
                          color={getChurnRiskColor(selectedCustomer.churn_risk) as any} 
                          size="small" 
                        />
                      </Typography>
                      {selectedCustomer.churn_risk.factors && (
                        <Box>
                          <Typography variant="subtitle2" sx={{ mt: 1 }}>Contributing Factors:</Typography>
                          <ul>
                            {Object.entries(selectedCustomer.churn_risk.factors).map(([key, value]: [string, any]) => (
                              <li key={key}>
                                <Typography variant="body2">
                                  {key.replace(/_/g, ' ')}: {typeof value === 'number' ? value.toFixed(2) : value}
                                </Typography>
                              </li>
                            ))}
                          </ul>
                        </Box>
                      )}
                      {selectedCustomer.churn_risk.recommendations && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2">Recommendations:</Typography>
                          <ul>
                            {selectedCustomer.churn_risk.recommendations.map((rec: string, i: number) => (
                              <li key={i}><Typography variant="body2">{rec}</Typography></li>
                            ))}
                          </ul>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Box>
              )}

              {/* Recent Calls */}
              <Typography variant="h6" gutterBottom>Recent Calls</Typography>
              {selectedCustomer.calls.length > 0 ? (
                <List>
                  {selectedCustomer.calls.map((call, i) => (
                    <React.Fragment key={call.id}>
                      <ListItem>
                        <ListItemIcon>
                          <Call />
                        </ListItemIcon>
                        <ListItemText
                          primary={`${call.duration_seconds}s call - ${call.status}`}
                          secondary={`${call.started_at ? new Date(call.started_at).toLocaleString() : 'Unknown'} | AI Confidence: ${call.ai_confidence ? `${(call.ai_confidence * 100).toFixed(0)}%` : 'N/A'}`}
                        />
                      </ListItem>
                      {i < selectedCustomer.calls.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Alert severity="info">No calls recorded</Alert>
              )}

              {/* Appointments */}
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Appointments</Typography>
              {selectedCustomer.appointments.length > 0 ? (
                <List>
                  {selectedCustomer.appointments.map((apt, i) => (
                    <React.Fragment key={apt.id}>
                      <ListItem>
                        <ListItemIcon>
                          <CalendarMonth />
                        </ListItemIcon>
                        <ListItemText
                          primary={`${apt.service_type || 'Service'} - ${apt.status}`}
                          secondary={apt.appointment_time ? new Date(apt.appointment_time).toLocaleString() : 'Unknown'}
                        />
                      </ListItem>
                      {i < selectedCustomer.appointments.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Alert severity="info">No appointments scheduled</Alert>
              )}
            </Box>
          ) : (
            <Alert severity="error">Failed to load customer details</Alert>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
