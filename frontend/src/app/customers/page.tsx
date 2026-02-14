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
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import LinearProgress from '@mui/material/LinearProgress';
import PersonIcon from '@mui/icons-material/Person';
import PhoneIcon from '@mui/icons-material/Phone';
import EmailIcon from '@mui/icons-material/Email';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import axios from 'axios';

interface Customer {
  id: number;
  name: string;
  phone: string;
  email?: string;
  totalCalls: number;
  lastCallDate: string;
  preferredServices: string[];
  notes: string;
  satisfactionScore: number;
  status: 'active' | 'inactive' | 'vip';
  appointmentHistory: Appointment[];
  callHistory: CallRecord[];
  churnRiskScore?: number;
  churnRiskLevel?: 'low' | 'medium' | 'high';
  vipTier?: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  engagementScore?: number;
}

interface Appointment {
  id: number;
  service: string;
  date: string;
  status: 'completed' | 'cancelled' | 'no-show';
}

interface CallRecord {
  id: number;
  date: string;
  duration: number;
  purpose: string;
  satisfaction: number;
  notes: string;
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

export default function CustomerDatabase() {
  const [tabValue, setTabValue] = useState(0);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerDetailOpen, setCustomerDetailOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        // Fetch call logs to build customer database
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const businessId = businessResponse.data[0].id;
          
          const callLogsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/call-logs/business/${businessId}`);
          const callLogs = callLogsResponse.data;
          
          const appointmentsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://receptium.onrender.com"}/api/appointments/business/${businessId}`);
          const appointments = appointmentsResponse.data;
          
          // Build customer profiles from call logs and appointments
          const customerMap = new Map<string, Customer>();
          
          // Process call logs
          callLogs.forEach((log: any, index: number) => {
            const phone = log.customer_phone;
            if (!customerMap.has(phone)) {
              customerMap.set(phone, {
                id: index + 1,
                name: `Customer ${index + 1}`,
                phone,
                email: `customer${index + 1}@example.com`,
                totalCalls: 0,
                lastCallDate: log.created_at,
                preferredServices: [],
                notes: '',
                satisfactionScore: Math.random() * 2 + 3, // Random score between 3-5
                status: Math.random() > 0.8 ? 'vip' : 'active',
                appointmentHistory: [],
                callHistory: [],
              });
            }
            
            const customer = customerMap.get(phone)!;
            customer.totalCalls++;
            customer.callHistory.push({
              id: log.id,
              date: log.created_at,
              duration: Math.floor(Math.random() * 300) + 60,
              purpose: 'General inquiry',
              satisfaction: Math.random() * 2 + 3,
              notes: log.transcript?.substring(0, 100) || 'No notes available',
            });
            
            if (new Date(log.created_at) > new Date(customer.lastCallDate)) {
              customer.lastCallDate = log.created_at;
            }
          });
          
          // Process appointments
          appointments.forEach((apt: any) => {
            const phone = apt.customer_phone;
            if (customerMap.has(phone)) {
              const customer = customerMap.get(phone)!;
              customer.name = apt.customer_name || customer.name;
              customer.appointmentHistory.push({
                id: apt.id,
                service: apt.service_type,
                date: apt.appointment_time,
                status: 'completed',
              });
              
              if (!customer.preferredServices.includes(apt.service_type)) {
                customer.preferredServices.push(apt.service_type);
              }
            }
          });
          
          const customersArray = Array.from(customerMap.values());
          setCustomers(customersArray);
          setFilteredCustomers(customersArray);
        }
      } catch (error) {
        console.error('Error fetching customer data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCustomers();
  }, []);

  useEffect(() => {
    let filtered = customers;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(customer =>
        customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customer.phone.includes(searchTerm) ||
        customer.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(customer => customer.status === statusFilter);
    }

    setFilteredCustomers(filtered);
  }, [customers, searchTerm, statusFilter]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCustomerDetail = (customer: Customer) => {
    setSelectedCustomer(customer);
    setCustomerDetailOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'vip': return 'warning';
      case 'active': return 'success';
      case 'inactive': return 'default';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const calculateCustomerValue = (customer: Customer) => {
    return customer.appointmentHistory.length * 100 + customer.totalCalls * 10;
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
          Customer Database
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage customer relationships and interaction history
        </Typography>
      </Box>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="All Customers" />
        <Tab label="Recent Interactions" />
        <Tab label="Customer Insights" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* All Customers */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardHeader
                title="Customer Directory"
                subheader={`${filteredCustomers.length} customers found`}
                action={
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      placeholder="Search customers..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      InputProps={{
                        startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                      sx={{ minWidth: 250 }}
                    />
                    <Button
                      variant="outlined"
                      startIcon={<FilterListIcon />}
                      onClick={() => {
                        setStatusFilter(statusFilter === 'all' ? 'vip' : 
                                      statusFilter === 'vip' ? 'active' : 
                                      statusFilter === 'active' ? 'inactive' : 'all');
                      }}
                    >
                      {statusFilter === 'all' ? 'All' : statusFilter.toUpperCase()}
                    </Button>
                  </Box>
                }
              />
              <CardContent sx={{ p: 0 }}>
                <List>
                  {filteredCustomers.map((customer) => (
                    <ListItem key={customer.id} divider>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          <PersonIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                            <Typography variant="subtitle1">{customer.name}</Typography>
                            <Chip
                              label={customer.status.toUpperCase()}
                              color={getStatusColor(customer.status) as any}
                              size="small"
                            />
                            {customer.vipTier && (
                              <Chip
                                label={customer.vipTier}
                                size="small"
                                color="warning"
                                variant="outlined"
                                sx={{ fontWeight: 'bold' }}
                              />
                            )}
                            {customer.churnRiskLevel && (
                              <Chip
                                label={`Risk: ${customer.churnRiskLevel.toUpperCase()}`}
                                size="small"
                                color={customer.churnRiskLevel === 'high' ? 'error' : customer.churnRiskLevel === 'medium' ? 'warning' : 'success'}
                                variant="outlined"
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <PhoneIcon fontSize="small" color="action" />
                                <Typography variant="body2">{customer.phone}</Typography>
                              </Box>
                              {customer.email && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <EmailIcon fontSize="small" color="action" />
                                  <Typography variant="body2">{customer.email}</Typography>
                                </Box>
                              )}
                            </Box>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                              <Typography variant="caption">
                                {customer.totalCalls} calls
                              </Typography>
                              <Typography variant="caption">
                                {customer.appointmentHistory.length} appointments
                              </Typography>
                              <Typography variant="caption">
                                Last contact: {formatDate(customer.lastCallDate)}
                              </Typography>
                              <Typography variant="caption">
                                Satisfaction: {customer.satisfactionScore.toFixed(1)}/5.0
                              </Typography>
                            </Box>
                            {customer.preferredServices.length > 0 && (
                              <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                {customer.preferredServices.slice(0, 3).map((service, index) => (
                                  <Chip key={index} label={service} size="small" variant="outlined" />
                                ))}
                              </Box>
                            )}
                          </Box>
                        }
                      />
                      <IconButton
                        edge="end"
                        onClick={() => handleCustomerDetail(customer)}
                        title="View Details"
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Recent Interactions */}
        <Card>
          <CardHeader title="Recent Customer Interactions" />
          <CardContent>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Customer</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Satisfaction</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {customers
                    .flatMap(customer => 
                      customer.callHistory.map(call => ({
                        ...call,
                        customerName: customer.name,
                        customerPhone: customer.phone,
                        customerId: customer.id,
                      }))
                    )
                    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                    .slice(0, 10)
                    .map((interaction) => (
                      <TableRow key={`${interaction.customerId}-${interaction.id}`}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {interaction.customerName}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {interaction.customerPhone}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip label="Phone Call" color="primary" size="small" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(interaction.date)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {Math.floor(interaction.duration / 60)}:{(interaction.duration % 60).toString().padStart(2, '0')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`${interaction.satisfaction.toFixed(1)}/5`}
                            color={interaction.satisfaction >= 4 ? 'success' : interaction.satisfaction >= 3 ? 'warning' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton size="small">
                            <VisibilityIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Customer Insights */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Top Customers by Value" />
              <CardContent>
                <List>
                  {customers
                    .sort((a, b) => calculateCustomerValue(b) - calculateCustomerValue(a))
                    .slice(0, 5)
                    .map((customer, index) => (
                      <ListItem key={customer.id}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: index === 0 ? 'warning.main' : 'primary.main' }}>
                            {index + 1}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={customer.name}
                          secondary={`Value: $${calculateCustomerValue(customer)}`}
                        />
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="High Satisfaction Customers" />
              <CardContent>
                <List>
                  {customers
                    .filter(c => c.satisfactionScore >= 4.5)
                    .slice(0, 5)
                    .map((customer) => (
                      <ListItem key={customer.id}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'success.main' }}>
                            <PersonIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={customer.name}
                          secondary={`${customer.satisfactionScore.toFixed(1)}/5.0 satisfaction`}
                        />
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Recent New Customers" />
              <CardContent>
                <List>
                  {customers
                    .sort((a, b) => new Date(b.lastCallDate).getTime() - new Date(a.lastCallDate).getTime())
                    .filter(c => c.totalCalls <= 2)
                    .slice(0, 5)
                    .map((customer) => (
                      <ListItem key={customer.id}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'info.main' }}>
                            <PersonIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={customer.name}
                          secondary={`Joined: ${formatDate(customer.lastCallDate)}`}
                        />
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Customer Detail Dialog */}
      <Dialog
        open={customerDetailOpen}
        onClose={() => setCustomerDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Customer Profile</DialogTitle>
        <DialogContent>
          {selectedCustomer && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Contact Information</Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body1"><strong>Name:</strong> {selectedCustomer.name}</Typography>
                  <Typography variant="body1"><strong>Phone:</strong> {selectedCustomer.phone}</Typography>
                  <Typography variant="body1"><strong>Email:</strong> {selectedCustomer.email || 'Not provided'}</Typography>
                  <Typography variant="body1">
                    <strong>Status:</strong>{' '}
                    <Chip
                      label={selectedCustomer.status.toUpperCase()}
                      color={getStatusColor(selectedCustomer.status) as any}
                      size="small"
                    />
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Statistics</Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body1"><strong>Total Calls:</strong> {selectedCustomer.totalCalls}</Typography>
                  <Typography variant="body1"><strong>Appointments:</strong> {selectedCustomer.appointmentHistory.length}</Typography>
                  <Typography variant="body1"><strong>Satisfaction:</strong> {selectedCustomer.satisfactionScore.toFixed(1)}/5.0</Typography>
                  <Typography variant="body1"><strong>Customer Value:</strong> ${calculateCustomerValue(selectedCustomer)}</Typography>
                </Box>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Preferred Services</Typography>
                <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedCustomer.preferredServices.map((service, index) => (
                    <Chip key={index} label={service} variant="outlined" />
                  ))}
                </Box>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Recent Call History</Typography>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Duration</TableCell>
                        <TableCell>Purpose</TableCell>
                        <TableCell>Satisfaction</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedCustomer.callHistory.slice(0, 5).map((call) => (
                        <TableRow key={call.id}>
                          <TableCell>{formatDate(call.date)}</TableCell>
                          <TableCell>
                            {Math.floor(call.duration / 60)}:{(call.duration % 60).toString().padStart(2, '0')}
                          </TableCell>
                          <TableCell>{call.purpose}</TableCell>
                          <TableCell>{call.satisfaction.toFixed(1)}/5</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCustomerDetailOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<EditIcon />}>
            Edit Customer
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}