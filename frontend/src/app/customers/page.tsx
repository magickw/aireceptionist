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
  Divider,
  Tooltip,
  Stack,
  LinearProgressProps
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
  SentimentDissatisfied,
  Diamond,
  EmojiEvents,
  MilitaryTech,
  WorkspacePremium,
  Groups,
  Lightbulb,
  ShoppingCart,
  AttachMoney,
  Schedule,
  Insights
} from '@mui/icons-material';
import api from '@/services/api';

interface Customer {
  phone: string;
  name?: string;
  email?: string;
  call_count: number;
  last_contact: string | null;
  avg_confidence: number;
  appointment_count: number;
  churn_risk: any;
  vip_status: any;
  loyalty_tier?: string;
  total_spent?: number;
  is_vip?: boolean;
}

interface CustomerDetails {
  phone: string;
  customer?: {
    name?: string;
    email?: string;
    loyalty_tier?: string;
    is_vip?: boolean;
    customer_since?: string;
  };
  metrics?: {
    total_calls?: number;
    total_orders?: number;
    total_appointments?: number;
    total_spent?: number;
    lifetime_value?: number;
    average_sentiment?: number;
    churn_risk?: number;
  };
  lifetime_value?: {
    historical?: number;
    projected_12_month?: number;
    average_transaction_value?: number;
    transactions_per_month?: number;
    confidence?: number;
  };
  calls: any[];
  appointments: any[];
  recent_activity?: any;
  churn_risk: any;
  vip_status: any;
  insights?: any[];
  recommendations?: string[];
  stats: any;
}

interface Insights {
  total_customers: number;
  vip_count: number;
  high_risk_count: number;
  segments?: any;
  top_customers?: any[];
  complaint_trends: any[];
  top_issues: any[];
}

// Loyalty tier configuration
const LOYALTY_CONFIG = {
  platinum: { color: '#E5E4E2', bgColor: '#1a1a2e', icon: Diamond, label: 'Platinum' },
  gold: { color: '#FFD700', bgColor: '#1a1a2e', icon: EmojiEvents, label: 'Gold' },
  silver: { color: '#C0C0C0', bgColor: '#1a1a2e', icon: MilitaryTech, label: 'Silver' },
  standard: { color: '#CD7F32', bgColor: '#1a1a2e', icon: WorkspacePremium, label: 'Standard' }
};

function LinearProgressWithLabel(props: LinearProgressProps & { value: number }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Box sx={{ width: '100%', mr: 1 }}>
        <LinearProgress variant="determinate" {...props} />
      </Box>
      <Box sx={{ minWidth: 35 }}>
        <Typography variant="body2" color="text.secondary">{`${Math.round(props.value)}%`}</Typography>
      </Box>
    </Box>
  );
}

function getLoyaltyTierConfig(tier: string | undefined) {
  return LOYALTY_CONFIG[tier as keyof typeof LOYALTY_CONFIG] || LOYALTY_CONFIG.standard;
}

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '$0';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
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
  
  // Segments view
  const [segmentsDialogOpen, setSegmentsDialogOpen] = useState(false);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCustomers, setTotalCustomers] = useState(0);

  useEffect(() => {
    fetchCustomers();
    fetchInsights();
  }, [page, tabValue]);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const res = await api.get('/customer-intelligence/customers', {
        params: { page, page_size: 20, sort_by: tabValue === 1 ? 'loyalty_tier' : tabValue === 2 ? 'total_spent' : 'last_contact' }
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
    const level = risk.risk_level || (risk > 0.6 ? 'high' : risk > 0.3 ? 'medium' : 'low');
    switch (level) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getChurnRiskIcon = (risk: any) => {
    if (!risk) return <SentimentNeutral />;
    const level = risk.risk_level || (risk > 0.6 ? 'high' : risk > 0.3 ? 'medium' : 'low');
    switch (level) {
      case 'high': return <SentimentDissatisfied />;
      case 'medium': return <SentimentNeutral />;
      case 'low': return <SentimentSatisfied />;
      default: return <SentimentNeutral />;
    }
  };

  const filteredCustomers = searchQuery
    ? customers.filter(c => c.phone.includes(searchQuery) || (c.name && c.name.toLowerCase().includes(searchQuery.toLowerCase())))
    : customers;

  // Render loyalty tier badge
  const renderLoyaltyBadge = (tier: string | undefined) => {
    const config = getLoyaltyTierConfig(tier);
    const IconComponent = config.icon;
    return (
      <Chip
        icon={<IconComponent sx={{ color: config.color }} />}
        label={config.label}
        size="small"
        sx={{
          bgcolor: config.bgColor,
          color: config.color,
          fontWeight: 'bold',
          border: `1px solid ${config.color}`,
          '& .MuiChip-icon': { color: config.color }
        }}
      />
    );
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Customer 360</Typography>
        <Stack direction="row" spacing={1}>
          <Button startIcon={<Groups />} onClick={() => setSegmentsDialogOpen(true)}>
            View Segments
          </Button>
          <Button startIcon={<Refresh />} onClick={() => { fetchCustomers(); fetchInsights(); }}>
            Refresh
          </Button>
        </Stack>
      </Box>

      {/* Insights Cards */}
      {insights && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%' }}>
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
            <Card sx={{ height: '100%', cursor: 'pointer' }} onClick={() => setSegmentsDialogOpen(true)}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', width: 56, height: 56 }}>
                  <Diamond />
                </Avatar>
                <Box>
                  <Typography variant="h4">{insights.vip_count}</Typography>
                  <Typography variant="body2" color="text.secondary">VIP Customers</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', width: 56, height: 56 }}>
                  <Warning />
                </Avatar>
                <Box>
                  <Typography variant="h4">{insights.high_risk_count}</Typography>
                  <Typography variant="body2" color="text.secondary">At Risk</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                  <AttachMoney />
                </Avatar>
                <Box>
                  <Typography variant="h5">
                    {insights.top_customers?.[0] ? formatCurrency(insights.top_customers[0].lifetime_value) : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Top LTV</Typography>
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
            <Tab label="VIP / Loyal" />
            <Tab label="At Risk" />
          </Tabs>
        </Box>
        
        <CardContent>
          {/* Search */}
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Search by phone or name..."
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
                      <TableCell>Loyalty Tier</TableCell>
                      <TableCell align="center">Calls</TableCell>
                      <TableCell align="center">Appts</TableCell>
                      <TableCell align="right">Total Spent</TableCell>
                      <TableCell align="center">Last Contact</TableCell>
                      <TableCell align="center">Churn Risk</TableCell>
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
                            <Avatar sx={{ width: 32, height: 32, bgcolor: customer.is_vip ? 'warning.main' : 'primary.main' }}>
                              {customer.name ? customer.name[0].toUpperCase() : <Phone fontSize="small" />}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {customer.name || customer.phone}
                              </Typography>
                              {customer.name && (
                                <Typography variant="caption" color="text.secondary">
                                  {customer.phone}
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          {renderLoyaltyBadge(customer.loyalty_tier)}
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
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="medium">
                            {formatCurrency(customer.total_spent)}
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
                              icon={getChurnRiskIcon(customer.churn_risk.risk_score || customer.churn_risk)}
                              label={customer.churn_risk.risk_level || 'Unknown'}
                              color={getChurnRiskColor(customer.churn_risk.risk_score || customer.churn_risk) as any}
                              size="small"
                            />
                          ) : (
                            <Chip label="Unknown" size="small" variant="outlined" />
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
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ width: 48, height: 48, bgcolor: selectedCustomer?.customer?.is_vip ? 'warning.main' : 'primary.main' }}>
              {selectedCustomer?.customer?.name ? selectedCustomer.customer.name[0].toUpperCase() : <Person />}
            </Avatar>
            <Box>
              <Typography variant="h6">
                {selectedCustomer?.customer?.name || selectedCustomer?.phone}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {renderLoyaltyBadge(selectedCustomer?.customer?.loyalty_tier)}
                {selectedCustomer?.customer?.is_vip && (
                  <Chip icon={<Star />} label="VIP" color="warning" size="small" />
                )}
              </Box>
            </Box>
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
              {/* Metrics Grid */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{selectedCustomer.metrics?.total_calls || selectedCustomer.stats?.total_calls || 0}</Typography>
                      <Typography variant="body2" color="text.secondary">Total Calls</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{selectedCustomer.metrics?.total_appointments || selectedCustomer.stats?.total_appointments || 0}</Typography>
                      <Typography variant="body2" color="text.secondary">Appointments</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {formatCurrency(selectedCustomer.lifetime_value?.historical || selectedCustomer.metrics?.total_spent || 0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">Lifetime Value</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      {selectedCustomer.churn_risk || selectedCustomer.metrics?.churn_risk ? (
                        <>
                          <Typography variant="h4" color={`${getChurnRiskColor(selectedCustomer.churn_risk?.risk_score || selectedCustomer.metrics?.churn_risk)}.main`}>
                            {Math.round((selectedCustomer.churn_risk?.risk_score || selectedCustomer.metrics?.churn_risk || 0) * 100)}%
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
              </Grid>

              {/* LTV Projection */}
              {selectedCustomer.lifetime_value && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>Lifetime Value Analysis</Typography>
                  <Card variant="outlined">
                    <CardContent>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2" color="text.secondary">Historical Value</Typography>
                          <Typography variant="h5" color="primary.main">
                            {formatCurrency(selectedCustomer.lifetime_value.historical)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2" color="text.secondary">Projected 12-Month</Typography>
                          <Typography variant="h5" color="success.main">
                            {formatCurrency(selectedCustomer.lifetime_value.projected_12_month)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2" color="text.secondary">Confidence</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgressWithLabel 
                              value={(selectedCustomer.lifetime_value.confidence || 0) * 100} 
                              sx={{ flexGrow: 1 }}
                            />
                          </Box>
                        </Grid>
                      </Grid>
                      {selectedCustomer.lifetime_value.average_transaction_value && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                          Avg. Transaction: {formatCurrency(selectedCustomer.lifetime_value.average_transaction_value)} | 
                          Transactions/Month: {selectedCustomer.lifetime_value.transactions_per_month?.toFixed(1)}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Box>
              )}

              {/* AI Insights */}
              {selectedCustomer.insights && selectedCustomer.insights.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Insights /> AI Insights
                  </Typography>
                  <Grid container spacing={2}>
                    {selectedCustomer.insights.map((insight: any, i: number) => (
                      <Grid item xs={12} sm={6} key={i}>
                        <Alert 
                          severity={insight.type === 'warning' ? 'warning' : insight.type === 'alert' ? 'error' : insight.type === 'positive' ? 'success' : 'info'}
                        >
                          <Typography variant="subtitle2">{insight.message}</Typography>
                          <Typography variant="body2">{insight.action}</Typography>
                        </Alert>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {/* Recommendations */}
              {selectedCustomer.recommendations && selectedCustomer.recommendations.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Lightbulb /> Recommendations
                  </Typography>
                  <Card variant="outlined">
                    <List dense>
                      {selectedCustomer.recommendations.map((rec: string, i: number) => (
                        <ListItem key={i}>
                          <ListItemIcon>
                            <TrendingUp color="primary" />
                          </ListItemIcon>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </Card>
                </Box>
              )}

              {/* Recent Activity */}
              {selectedCustomer.recent_activity && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>Recent Activity</Typography>
                  <Grid container spacing={2}>
                    {/* Recent Calls */}
                    <Grid item xs={12} md={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Call /> Recent Calls
                          </Typography>
                          {selectedCustomer.recent_activity.calls?.length > 0 ? (
                            <List dense>
                              {selectedCustomer.recent_activity.calls.slice(0, 5).map((call: any, i: number) => (
                                <ListItem key={i}>
                                  <ListItemText
                                    primary={`${call.duration_seconds || 0}s call`}
                                    secondary={call.date ? new Date(call.date).toLocaleDateString() : 'Unknown'}
                                  />
                                  {call.sentiment && (
                                    <Chip 
                                      label={call.sentiment} 
                                      size="small"
                                      color={call.sentiment === 'positive' ? 'success' : call.sentiment === 'negative' ? 'error' : 'default'}
                                    />
                                  )}
                                </ListItem>
                              ))}
                            </List>
                          ) : (
                            <Typography variant="body2" color="text.secondary">No recent calls</Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                    
                    {/* Recent Orders */}
                    <Grid item xs={12} md={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ShoppingCart /> Recent Orders
                          </Typography>
                          {selectedCustomer.recent_activity.orders?.length > 0 ? (
                            <List dense>
                              {selectedCustomer.recent_activity.orders.slice(0, 5).map((order: any, i: number) => (
                                <ListItem key={i}>
                                  <ListItemText
                                    primary={formatCurrency(order.total)}
                                    secondary={order.date ? new Date(order.date).toLocaleDateString() : 'Unknown'}
                                  />
                                  <Chip label={order.status} size="small" />
                                </ListItem>
                              ))}
                            </List>
                          ) : (
                            <Typography variant="body2" color="text.secondary">No recent orders</Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </Box>
              )}

              {/* Appointments */}
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Appointments</Typography>
              {selectedCustomer.appointments?.length > 0 || selectedCustomer.recent_activity?.appointments?.length > 0 ? (
                <List>
                  {(selectedCustomer.recent_activity?.appointments || selectedCustomer.appointments || []).map((apt: any, i: number) => (
                    <React.Fragment key={i}>
                      <ListItem>
                        <ListItemIcon>
                          <CalendarMonth />
                        </ListItemIcon>
                        <ListItemText
                          primary={`${apt.service_type || 'Service'} - ${apt.status}`}
                          secondary={apt.appointment_time || apt.date ? new Date(apt.appointment_time || apt.date).toLocaleString() : 'Unknown'}
                        />
                      </ListItem>
                      {i < (selectedCustomer.recent_activity?.appointments?.length || selectedCustomer.appointments?.length || 0) - 1 && <Divider />}
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

      {/* Segments Dialog */}
      <Dialog 
        open={segmentsDialogOpen} 
        onClose={() => setSegmentsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Customer Segments</DialogTitle>
        <DialogContent>
          {insights?.segments ? (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Total Customers: {insights.segments.total_customers || 0}
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(insights.segments.segments || {}).map(([key, segment]: [string, any]) => (
                  <Grid item xs={12} sm={6} md={4} key={key}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>{key.replace('_', ' ')}</Typography>
                        <Typography variant="h3" color="primary">{segment.count || 0}</Typography>
                        <Typography variant="body2" color="text.secondary">customers</Typography>
                        {segment.customers && segment.customers.length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="caption" color="text.secondary">Top customers:</Typography>
                            <List dense>
                              {segment.customers.slice(0, 3).map((c: any, i: number) => (
                                <ListItem key={i} sx={{ py: 0 }}>
                                  <ListItemText 
                                    primary={c.name || c.phone}
                                    secondary={c.days_inactive ? `${c.days_inactive} days inactive` : c.risk ? `${Math.round(c.risk * 100)}% risk` : undefined}
                                  />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSegmentsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}