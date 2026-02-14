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
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Divider from '@mui/material/Divider';
import Avatar from '@mui/material/Avatar';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import BusinessIcon from '@mui/icons-material/Business';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import SpaIcon from '@mui/icons-material/Spa';
import axios from 'axios';

interface BusinessProfile {
  id?: number;
  name: string;
  type: string;
  phone: string;
  address: string;
  description: string;
  website: string;
  operatingHours: { [key: number]: { open: number; close: number; closed: boolean } };
}

interface Service {
  id?: number;
  name: string;
  description: string;
  duration: number;
  price: number;
  category: string;
}

export default function BusinessSetup() {
  const [profile, setProfile] = useState<BusinessProfile>({
    name: '',
    type: '',
    phone: '',
    address: '',
    description: '',
    website: '',
    operatingHours: {
      0: { open: 9, close: 17, closed: false }, // Sunday
      1: { open: 9, close: 17, closed: false }, // Monday
      2: { open: 9, close: 17, closed: false }, // Tuesday
      3: { open: 9, close: 17, closed: false }, // Wednesday
      4: { open: 9, close: 17, closed: false }, // Thursday
      5: { open: 9, close: 17, closed: false }, // Friday
      6: { open: 9, close: 17, closed: false }, // Saturday
    },
  });
  
  const [services, setServices] = useState<Service[]>([]);
  const [serviceDialogOpen, setServiceDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [newService, setNewService] = useState<Service>({
    name: '',
    description: '',
    duration: 30,
    price: 0,
    category: '',
  });

  const businessTypes = [
    { value: 'restaurant', label: 'Restaurant', icon: <RestaurantIcon /> },
    { value: 'salon', label: 'Hair Salon', icon: <ContentCutIcon /> },
    { value: 'spa', label: 'Spa & Wellness', icon: <SpaIcon /> },
    { value: 'medical', label: 'Medical Practice', icon: <BusinessIcon /> },
    { value: 'dental', label: 'Dental Office', icon: <BusinessIcon /> },
    { value: 'fitness', label: 'Fitness Center', icon: <BusinessIcon /> },
    { value: 'automotive', label: 'Auto Service', icon: <BusinessIcon /> },
    { value: 'legal', label: 'Law Firm', icon: <BusinessIcon /> },
    { value: 'accounting', label: 'Accounting', icon: <BusinessIcon /> },
    { value: 'consulting', label: 'Consulting', icon: <BusinessIcon /> },
    { value: 'real-estate', label: 'Real Estate', icon: <BusinessIcon /> },
    { value: 'veterinary', label: 'Veterinary Clinic', icon: <BusinessIcon /> },
    { value: 'retail', label: 'Retail Store', icon: <BusinessIcon /> },
    { value: 'cleaning', label: 'Cleaning Service', icon: <BusinessIcon /> },
    { value: 'education', label: 'Education/Tutoring', icon: <BusinessIcon /> },
    { value: 'photography', label: 'Photography Studio', icon: <BusinessIcon /> },
    { value: 'plumbing', label: 'Plumbing Service', icon: <BusinessIcon /> },
    { value: 'electrical', label: 'Electrical Service', icon: <BusinessIcon /> },
    { value: 'landscaping', label: 'Landscaping', icon: <BusinessIcon /> },
    { value: 'insurance', label: 'Insurance Agency', icon: <BusinessIcon /> },
    { value: 'other', label: 'Other', icon: <BusinessIcon /> },
  ];

  const daysOfWeek = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'
  ];

  useEffect(() => {
    const fetchBusinessData = async () => {
      try {
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const business = businessResponse.data[0];
          const settings = business.settings || {};
          
          // Define default operating hours
          const defaultOperatingHours = {
            0: { open: 9, close: 17, closed: false },
            1: { open: 9, close: 17, closed: false },
            2: { open: 9, close: 17, closed: false },
            3: { open: 9, close: 17, closed: false },
            4: { open: 9, close: 17, closed: false },
            5: { open: 9, close: 17, closed: false },
            6: { open: 10, close: 16, closed: false },
          };
          
          setProfile({
            id: business.id,
            name: business.name || '',
            type: business.type || '',
            phone: settings.phone || '',
            address: settings.address || '',
            description: settings.description || '',
            website: settings.website || '',
            operatingHours: business.operating_hours || defaultOperatingHours,
          });
          
          // Load services from settings if available
          if (settings.services) {
            setServices(settings.services);
          } else {
            // Default services if none exist
            setServices([
              {
                id: 1,
                name: 'Consultation',
                description: 'Initial consultation with our AI receptionist',
                duration: 15,
                price: 0,
                category: 'General',
              },
              {
                id: 2,
                name: 'Appointment Booking',
                description: 'Book appointments through AI assistant',
                duration: 5,
                price: 0,
                category: 'Booking',
              },
            ]);
          }
        }
      } catch (error) {
        console.error('Error fetching business data:', error);
      }
    };

    fetchBusinessData();
  }, []);

  const handleProfileSave = async () => {
    try {
      // Prepare settings object with additional business info
      const businessSettings = {
        phone: profile.phone,
        address: profile.address,
        description: profile.description,
        website: profile.website,
        services: services,
      };

      if (profile.id) {
        await axios.put(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses/${profile.id}`, {
          name: profile.name,
          type: profile.type,
          settings: businessSettings,
          operating_hours: profile.operatingHours,
        });
      } else {
        const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`, {
          name: profile.name,
          type: profile.type,
          settings: businessSettings,
          operating_hours: profile.operatingHours,
        });
        setProfile({ ...profile, id: response.data.id });
      }
      alert('Business profile saved successfully!');
    } catch (error) {
      console.error('Error saving business profile:', error);
      alert('Failed to save business profile.');
    }
  };

  const handleHoursChange = (day: number, field: 'open' | 'close' | 'closed', value: number | boolean) => {
    setProfile({
      ...profile,
      operatingHours: {
        ...profile.operatingHours,
        [day]: { ...profile.operatingHours[day], [field]: value },
      },
    });
  };

  const handleServiceSave = () => {
    if (editingService) {
      setServices(services.map(s => s.id === editingService.id ? { ...newService, id: editingService.id } : s));
    } else {
      setServices([...services, { ...newService, id: Date.now() }]);
    }
    setServiceDialogOpen(false);
    setEditingService(null);
    setNewService({ name: '', description: '', duration: 30, price: 0, category: '' });
  };

  const handleServiceEdit = (service: Service) => {
    setEditingService(service);
    setNewService({ ...service });
    setServiceDialogOpen(true);
  };

  const handleServiceDelete = (serviceId: number) => {
    setServices(services.filter(s => s.id !== serviceId));
  };

  const getBusinessTypeIcon = (type: string) => {
    const businessType = businessTypes.find(bt => bt.value === type);
    return businessType ? businessType.icon : <BusinessIcon />;
  };

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
          Business Setup
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          Configure your business profile, services, and operating hours for AI training
        </Typography>
      </Box>

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* Business Profile */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: 'primary.main', width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                  {getBusinessTypeIcon(profile.type)}
                </Avatar>
              }
              title={
                <Typography variant="h6" sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}>
                  Business Profile
                </Typography>
              }
              subheader={
                <Typography variant="body2" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                  Basic information about your business
                </Typography>
              }
            />
            <CardContent>
              <Grid container spacing={{ xs: 2, sm: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Business Name"
                    variant="outlined"
                    fullWidth
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    required
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl variant="outlined" fullWidth size="small">
                    <InputLabel>Business Type</InputLabel>
                    <Select
                      value={profile.type}
                      onChange={(e) => setProfile({ ...profile, type: e.target.value })}
                      label="Business Type"
                    >
                      {businessTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {type.icon}
                            <Typography sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                              {type.label}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Phone Number"
                    variant="outlined"
                    fullWidth
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Website"
                    variant="outlined"
                    fullWidth
                    value={profile.website}
                    onChange={(e) => setProfile({ ...profile, website: e.target.value })}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Address"
                    variant="outlined"
                    fullWidth
                    value={profile.address}
                    onChange={(e) => setProfile({ ...profile, address: e.target.value })}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Description"
                    variant="outlined"
                    fullWidth
                    multiline
                    rows={3}
                    value={profile.description}
                    onChange={(e) => setProfile({ ...profile, description: e.target.value })}
                    helperText="Describe your business to help AI provide better responses"
                    size="small"
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 3, display: 'flex', justifyContent: { xs: 'stretch', sm: 'flex-end' } }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleProfileSave}
                  sx={{ minWidth: { xs: '100%', sm: 120 } }}
                  size="medium"
                >
                  Save Profile
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Operating Hours */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 'fit-content' }}>
            <CardHeader
              title={
                <Typography variant="h6" sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}>
                  Operating Hours
                </Typography>
              }
              subheader={
                <Typography variant="body2" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                  Configure your business hours
                </Typography>
              }
            />
            <CardContent>
              {daysOfWeek.map((dayName, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 1, sm: 0 } }}>
                    <Typography sx={{ width: { xs: '100%', sm: 100 }, fontWeight: 'medium', textAlign: { xs: 'center', sm: 'left' }, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                      {dayName}
                    </Typography>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={!profile.operatingHours[index]?.closed}
                          onChange={(e) => handleHoursChange(index, 'closed', !e.target.checked)}
                          size="small"
                        />
                      }
                      label="Open"
                      sx={{ ml: { xs: 0, sm: 'auto' } }}
                    />
                  </Box>
                  {!profile.operatingHours[index]?.closed && (
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexDirection: { xs: 'column', sm: 'row' } }}>
                      <FormControl variant="outlined" size="small" sx={{ minWidth: { xs: '100%', sm: 80 } }}>
                        <InputLabel>Open</InputLabel>
                        <Select
                          value={profile.operatingHours[index]?.open || 0}
                          onChange={(e) => handleHoursChange(index, 'open', e.target.value as number)}
                          label="Open"
                        >
                          {[...Array(24).keys()].map((hour) => (
                            <MenuItem key={hour} value={hour}>
                              {`${hour}:00`}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' } }}>to</Typography>
                      <FormControl variant="outlined" size="small" sx={{ minWidth: { xs: '100%', sm: 80 } }}>
                        <InputLabel>Close</InputLabel>
                        <Select
                          value={profile.operatingHours[index]?.close || 0}
                          onChange={(e) => handleHoursChange(index, 'close', e.target.value as number)}
                          label="Close"
                        >
                          {[...Array(24).keys()].map((hour) => (
                            <MenuItem key={hour} value={hour}>
                              {`${hour}:00`}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Box>
                  )}
                  {index < daysOfWeek.length - 1 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Services & Menu */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title={
                <Typography variant="h6" sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}>
                  Services & Menu
                </Typography>
              }
              subheader={
                <Typography variant="body2" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                  Configure services for AI booking and information
                </Typography>
              }
              action={
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setEditingService(null);
                    setNewService({ name: '', description: '', duration: 30, price: 0, category: '' });
                    setServiceDialogOpen(true);
                  }}
                  size="small"
                  sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                >
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Add Service</Box>
                  <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>Add</Box>
                </Button>
              }
            />
            <CardContent>
              {services.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: { xs: 3, sm: 4 } }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                    No services configured. Add services to help AI provide better information.
                  </Typography>
                </Box>
              ) : (
                <List>
                  {services.map((service) => (
                    <ListItem key={service.id} divider sx={{ flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'stretch', sm: 'center' }, py: { xs: 2, sm: 1 } }}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexDirection: { xs: 'column', sm: 'row' }, textAlign: { xs: 'center', sm: 'left' } }}>
                            <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.125rem' } }}>
                              {service.name}
                            </Typography>
                            <Chip label={service.category} size="small" color="primary" />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ textAlign: { xs: 'center', sm: 'left' } }}>
                            <Typography variant="body2" component="span" color="text.primary" sx={{ mb: 1, display: 'block', fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                              {service.description}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 2, justifyContent: { xs: 'center', sm: 'flex-start' }, flexWrap: 'wrap' }}>
                              <Chip label={`${service.duration} min`} size="small" variant="outlined" />
                              <Chip label={`$${service.price}`} size="small" variant="outlined" />
                            </Box>
                          </Box>
                        }
                        sx={{ flex: 1 }}
                      />
                      <ListItemSecondaryAction sx={{ position: { xs: 'static', sm: 'absolute' }, right: { xs: 'auto', sm: 16 }, display: 'flex', gap: 1, mt: { xs: 2, sm: 0 }, justifyContent: { xs: 'center', sm: 'flex-end' } }}>
                        <IconButton
                          edge="end"
                          aria-label="edit"
                          onClick={() => handleServiceEdit(service)}
                          size="small"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          edge="end"
                          aria-label="delete"
                          onClick={() => service.id && handleServiceDelete(service.id)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Service Dialog */}
      <Dialog
        open={serviceDialogOpen}
        onClose={() => setServiceDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            m: { xs: 2, sm: 3 },
            maxHeight: { xs: 'calc(100vh - 64px)', sm: 'calc(100vh - 128px)' }
          }
        }}
      >
        <DialogTitle sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}>
          {editingService ? 'Edit Service' : 'Add New Service'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Service Name"
                variant="outlined"
                fullWidth
                value={newService.name}
                onChange={(e) => setNewService({ ...newService, name: e.target.value })}
                required
                size={{ xs: 'small', sm: 'medium' }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                variant="outlined"
                fullWidth
                multiline
                rows={2}
                value={newService.description}
                onChange={(e) => setNewService({ ...newService, description: e.target.value })}
                size={{ xs: 'small', sm: 'medium' }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                label="Duration (minutes)"
                variant="outlined"
                fullWidth
                type="number"
                value={newService.duration}
                onChange={(e) => setNewService({ ...newService, duration: parseInt(e.target.value) || 0 })}
                size={{ xs: 'small', sm: 'medium' }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                label="Price ($)"
                variant="outlined"
                fullWidth
                type="number"
                value={newService.price}
                onChange={(e) => setNewService({ ...newService, price: parseFloat(e.target.value) || 0 })}
                size={{ xs: 'small', sm: 'medium' }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Category"
                variant="outlined"
                fullWidth
                value={newService.category}
                onChange={(e) => setNewService({ ...newService, category: e.target.value })}
                helperText="e.g., Hair Services, Treatments, Consultation"
                size={{ xs: 'small', sm: 'medium' }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: { xs: 2, sm: 3 }, flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 1, sm: 0 } }}>
          <Button 
            onClick={() => setServiceDialogOpen(false)}
            fullWidth
          >
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleServiceSave}
            fullWidth
          >
            {editingService ? 'Update' : 'Add'} Service
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}