'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress, 
  Grid, Chip, IconButton, Alert, FormControl, InputLabel, Select, MenuItem,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Dialog, DialogTitle, DialogContent, DialogActions, Switch, FormControlLabel
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import api from '@/services/api';

interface OperatingHours {
  [key: string]: { open: string; close: string; closed: boolean };
}

interface BusinessSettings {
  services: string[];
}

interface PricingItem {
  id?: number;
  name: string;
  description: string;
  price: number | null;
  unit: string;
  category: string;
  available: boolean;
  is_active: boolean;
  inventory: number;
}

const BUSINESS_TYPES = [
  { value: 'general', label: 'General Business' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'hotel', label: 'Hotel' },
  { value: 'dental', label: 'Dental Clinic' },
  { value: 'medical', label: 'Medical Clinic' },
  { value: 'law_firm', label: 'Law Firm' },
  { value: 'salon', label: 'Salon / Spa' },
  { value: 'retail', label: 'Retail Store' },
  { value: 'auto_repair', label: 'Auto Repair' },
];

const UNITS = [
  { value: 'per item', label: 'Per Item' },
  { value: 'per piece', label: 'Per Piece' },
  { value: 'per serving', label: 'Per Serving' },
  { value: 'per lb', label: 'Per Pound (lb)' },
  { value: 'per kg', label: 'Per Kilogram (kg)' },
  { value: 'per hour', label: 'Per Hour' },
  { value: 'per day', label: 'Per Day' },
  { value: 'per ton', label: 'Per Ton' },
  { value: 'per meter', label: 'Per Meter' },
  { value: 'per roll', label: 'Per Roll' },
  { value: 'per box', label: 'Per Box' },
  { value: 'per pack', label: 'Per Pack' },
];

const CATEGORIES = [
  'Main Course', 'Appetizers', 'Desserts', 'Drinks',
  'Services', 'Products', 'Consultation', 'Treatment', 'Other'
];

export default function BusinessSetupPage() {
  const [profile, setProfile] = useState<{
    id?: number; 
    name: string; 
    type: string;
    phone: string;
    address: string;
    website: string;
    description: string;
    business_license: string;
    operating_hours: OperatingHours;
    settings: BusinessSettings;
  }>({ 
    name: '', 
    type: 'general',
    phone: '',
    address: '',
    website: '',
    description: '',
    business_license: '',
    operating_hours: {
      monday: { open: '09:00', close: '17:00', closed: false },
      tuesday: { open: '09:00', close: '17:00', closed: false },
      wednesday: { open: '09:00', close: '17:00', closed: false },
      thursday: { open: '09:00', close: '17:00', closed: false },
      friday: { open: '09:00', close: '17:00', closed: false },
      saturday: { open: '10:00', close: '14:00', closed: false },
      sunday: { open: '', close: '', closed: true },
    },
    settings: { services: [] }
  });
  
  // Pricing state
  const [pricingItems, setPricingItems] = useState<PricingItem[]>([]);
  const [pricingLoading, setPricingLoading] = useState(true);
  const [pricingDialogOpen, setPricingDialogOpen] = useState(false);
  const [editingPricingItem, setEditingPricingItem] = useState<PricingItem | null>(null);
  const [pricingSaving, setPricingSaving] = useState(false);
  
  const emptyPricingItem: PricingItem = {
    name: '',
    description: '',
    price: null,
    unit: 'per item',
    category: 'Services',
    available: true,
    is_active: true,
    inventory: 1,
  };
  
  const [pricingFormData, setPricingFormData] = useState<PricingItem>(emptyPricingItem);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [newService, setNewService] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/businesses');
        if (res.data.length > 0) {
          const data = res.data[0];
          setProfile({
            ...data,
            operating_hours: data.operating_hours || profile.operating_hours,
            settings: data.settings || { services: [] }
          });
          
          // Also fetch pricing items for this business
          fetchPricingItems(data.id);
        }
      } catch (error) { 
        console.error('Failed to fetch profile', error); 
      }
      finally { setLoading(false); }
    };
    fetchProfile();
  }, []);

  const fetchPricingItems = async (businessId: number) => {
    setPricingLoading(true);
    try {
      const res = await api.get('/menu/', { params: { business_id: businessId } });
      setPricingItems(res.data);
    } catch (error) {
      console.error('Failed to fetch pricing items', error);
    } finally {
      setPricingLoading(false);
    }
  };

  const handleSavePricing = async () => {
    if (!profile.id) {
      alert('Please save the business profile first.');
      return;
    }
    
    setPricingSaving(true);
    try {
      const payload = {
        ...pricingFormData,
        price: pricingFormData.price ? parseFloat(String(pricingFormData.price)) : null,
        inventory: pricingFormData.inventory ? parseInt(String(pricingFormData.inventory), 10) : 1,
      };
      
      if (editingPricingItem?.id) {
        await api.put(`/menu/${editingPricingItem.id}`, payload, { params: { business_id: profile.id } });
      } else {
        await api.post('/menu/', payload, { params: { business_id: profile.id } });
      }
      
      setPricingDialogOpen(false);
      fetchPricingItems(profile.id);
      setPricingFormData(emptyPricingItem);
      setEditingPricingItem(null);
    } catch (error) {
      console.error('Failed to save pricing item', error);
      alert('Failed to save pricing item.');
    } finally {
      setPricingSaving(false);
    }
  };

  const handleEditPricing = (item: PricingItem) => {
    setEditingPricingItem(item);
    setPricingFormData(item);
    setPricingDialogOpen(true);
  };

  const handleDeletePricing = async (id: number) => {
    if (!profile.id) return;
    if (!confirm('Are you sure you want to delete this item?')) return;
    try {
      await api.delete(`/menu/${id}`, { params: { business_id: profile.id } });
      fetchPricingItems(profile.id);
    } catch (error) {
      console.error('Failed to delete pricing item', error);
    }
  };

  const handleAddNewPricing = () => {
    setEditingPricingItem(null);
    setPricingFormData(emptyPricingItem);
    setPricingDialogOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...profile,
        operating_hours: profile.operating_hours,
        settings: profile.settings
      };
      if (profile.id) {
        const res = await api.put(`/businesses/${profile.id}`, payload);
        // Ensure state is updated with any changes from backend
        if (res.data) {
          setProfile(p => ({ ...p, ...res.data }));
        }
      } else {
        const res = await api.post('/businesses', payload);
        if (res.data) {
          setProfile(p => ({ ...p, ...res.data }));
          // If this was first create, we should now be able to add pricing
        }
      }
      alert('Profile Saved!');
    } catch (error) {
      console.error('Failed to save profile', error);
      alert('Failed to save profile.');
    } finally { setSaving(false); }
  };

  const addService = () => {
    if (newService.trim()) {
      setProfile(p => ({
        ...p,
        settings: { ...p.settings, services: [...p.settings.services, newService.trim()] }
      }));
      setNewService('');
    }
  };

  const removeService = (index: number) => {
    setProfile(p => ({
      ...p,
      settings: { ...p.settings, services: p.settings.services.filter((_: any, i: number) => i !== index) }
    }));
  };

  const updateHours = (day: string, field: string, value: any) => {
    setProfile(p => ({
      ...p,
      operating_hours: {
        ...p.operating_hours,
        [day]: { ...p.operating_hours[day], [field]: value }
      }
    }));
  };

  if (loading) return <Container sx={{p:4}}><LinearProgress/></Container>;

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Business Setup</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure your business information to help the AI assistant understand your business better.
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Basic Information</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Business Name" value={profile.name} onChange={(e) => setProfile(p => ({...p, name: e.target.value}))} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth margin="normal">
                            <InputLabel>Business Type</InputLabel>
                            <Select
                              value={profile.type}
                              label="Business Type"
                              onChange={(e) => setProfile(p => ({...p, type: e.target.value}))}
                            >
                              {BUSINESS_TYPES.map((bt) => (
                                <MenuItem key={bt.value} value={bt.value}>{bt.label}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Phone Number" value={profile.phone} onChange={(e) => setProfile(p => ({...p, phone: e.target.value}))} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth margin="normal" label="Website" value={profile.website} onChange={(e) => setProfile(p => ({...p, website: e.target.value}))} placeholder="https://" />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth margin="normal" label="Address" value={profile.address} onChange={(e) => setProfile(p => ({...p, address: e.target.value}))} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth margin="normal" label="Business License Number (Optional)" value={profile.business_license} onChange={(e) => setProfile(p => ({...p, business_license: e.target.value}))} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth margin="normal" label="Description" multiline rows={3} value={profile.description} onChange={(e) => setProfile(p => ({...p, description: e.target.value}))} placeholder="Brief description of your business for AI context..." />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mb: 4 }}>
        <Button variant="contained" size="large" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Profile'}
        </Button>
      </Box>

      {/* Pricing & Products Management Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AttachMoneyIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Products, Services & Pricing</Typography>
            </Box>
            <Button 
              variant="outlined" 
              startIcon={<AddIcon />} 
              size="small"
              onClick={handleAddNewPricing}
              disabled={!profile.id}
            >
              Add Item
            </Button>
          </Box>
          
          <Alert severity="info" sx={{ mb: 2, py: 0 }}>
            List your products and services with their prices. This information is critical for the AI to accurately answer customer questions about costs.
          </Alert>
          
          {!profile.id && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Please save your business profile above before adding products or services.
            </Alert>
          )}

          {pricingLoading ? (
            <LinearProgress sx={{ my: 2 }} />
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pricingItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell sx={{ fontWeight: 'medium' }}>{item.name}</TableCell>
                      <TableCell><Chip label={item.category} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} /></TableCell>
                      <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                        {item.price ? `$${item.price.toFixed(2)}` : '-'}
                        <Typography variant="caption" sx={{ ml: 0.5, color: 'text.secondary' }}>{item.unit}</Typography>
                      </TableCell>
                      <TableCell align="center">
                        <IconButton size="small" onClick={() => handleEditPricing(item)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDeletePricing(item.id!)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                  {pricingItems.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                          No products or services added yet.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Service Categories (Keywords)</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Add specific service keywords. This helps the AI understand the general categories of work you do.
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            {profile.settings.services.map((service: string, index: number) => (
              <Chip key={index} label={service} onDelete={() => removeService(index)} deleteIcon={<DeleteIcon />} />
            ))}
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField size="small" label="Add Service Keyword" value={newService} onChange={(e) => setNewService(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addService())} />
            <Button variant="outlined" startIcon={<AddIcon />} onClick={addService}>Add</Button>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Operating Hours</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Set your business hours for each day of the week.
          </Typography>
          {Object.entries(profile.operating_hours).map(([day, hours]) => (
            <Grid container spacing={2} key={day} alignItems="center" sx={{ mb: 1 }}>
              <Grid item xs={12} sm={3}>
                <Typography textTransform="capitalize">{day}</Typography>
              </Grid>
              <Grid item xs={12} sm={2}>
                <TextField size="small" type="time" fullWidth value={hours.open} onChange={(e) => updateHours(day, 'open', e.target.value)} disabled={hours.closed} />
              </Grid>
              <Grid item xs={12} sm={2}>
                <TextField size="small" type="time" fullWidth value={hours.close} onChange={(e) => updateHours(day, 'close', e.target.value)} disabled={hours.closed} />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Button size="small" variant={hours.closed ? "contained" : "outlined"} color={hours.closed ? "error" : "primary"} onClick={() => updateHours(day, 'closed', !hours.closed)}>
                  {hours.closed ? "Closed" : "Open"}
                </Button>
              </Grid>
            </Grid>
          ))}
        </CardContent>
      </Card>

      {/* Pricing Dialog */}
      <Dialog open={pricingDialogOpen} onClose={() => setPricingDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingPricingItem ? 'Edit Product/Service' : 'Add Product/Service'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={pricingFormData.name}
                onChange={(e) => setPricingFormData({ ...pricingFormData, name: e.target.value })}
                required
                placeholder="e.g., Kung Pow Chicken, Haircut, Legal Consultation"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Price"
                type="number"
                InputProps={{ startAdornment: '$' }}
                value={pricingFormData.price || ''}
                onChange={(e) => setPricingFormData({ ...pricingFormData, price: e.target.value ? parseFloat(e.target.value) : null })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Unit</InputLabel>
                <Select
                  value={pricingFormData.unit}
                  label="Unit"
                  onChange={(e) => setPricingFormData({ ...pricingFormData, unit: e.target.value })}
                >
                  {UNITS.map(u => (
                    <MenuItem key={u.value} value={u.value}>{u.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={pricingFormData.category}
                  label="Category"
                  onChange={(e) => setPricingFormData({ ...pricingFormData, category: e.target.value })}
                >
                  {CATEGORIES.map(cat => (
                    <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={pricingFormData.description}
                onChange={(e) => setPricingFormData({ ...pricingFormData, description: e.target.value })}
                placeholder="Brief description of the product/service"
              />
            </Grid>
            {profile.type === 'hotel' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Inventory (e.g., Number of Rooms)"
                  type="number"
                  value={pricingFormData.inventory || ''}
                  onChange={(e) => setPricingFormData({ ...pricingFormData, inventory: e.target.value ? parseInt(e.target.value, 10) : 1 })}
                />
              </Grid>
            )}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={pricingFormData.available}
                    onChange={(e) => setPricingFormData({ ...pricingFormData, available: e.target.checked })}
                  />
                }
                label="Available for ordering/booking"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPricingDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSavePricing} variant="contained" disabled={pricingSaving || !pricingFormData.name}>
            {pricingSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
