'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress, 
  Grid, Chip, IconButton, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, Alert, Switch, FormControlLabel
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import api from '@/services/api';

interface PricingItem {
  id?: number;
  name: string;
  description: string;
  price: number | null;
  category: string;
  available: boolean;
  is_active: boolean;
}

const CATEGORIES = [
  'Main Course', 'Appetizers', 'Desserts', 'Drinks',
  'Services', 'Products', 'Consultation', 'Treatment', 'Other'
];

export default function PricingPage() {
  const [items, setItems] = useState<PricingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<PricingItem | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('');

  const emptyItem: PricingItem = {
    name: '',
    description: '',
    price: null,
    category: 'Services',
    available: true,
    is_active: true
  };

  const [formData, setFormData] = useState<PricingItem>(emptyItem);

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    try {
      const res = await api.get('/menu/', { params: { business_id: 1 } });
      setItems(res.data);
    } catch (error) {
      console.error('Failed to fetch pricing items', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...formData,
        price: formData.price ? parseFloat(String(formData.price)) : null
      };
      
      if (editingItem?.id) {
        await api.put(`/menu/${editingItem.id}`, payload, { params: { business_id: 1 } });
      } else {
        await api.post('/menu/', payload, { params: { business_id: 1 } });
      }
      
      setDialogOpen(false);
      fetchItems();
      setFormData(emptyItem);
      setEditingItem(null);
    } catch (error) {
      console.error('Failed to save pricing item', error);
      alert('Failed to save pricing item.');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item: PricingItem) => {
    setEditingItem(item);
    setFormData(item);
    setDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this item?')) return;
    try {
      await api.delete(`/menu/${id}`, { params: { business_id: 1 } });
      fetchItems();
    } catch (error) {
      console.error('Failed to delete pricing item', error);
    }
  };

  const handleAddNew = () => {
    setEditingItem(null);
    setFormData(emptyItem);
    setDialogOpen(true);
  };

  const filteredItems = categoryFilter 
    ? items.filter(item => item.category === categoryFilter)
    : items;

  const totalItems = items.length;
  const pricedItems = items.filter(i => i.price);
  const avgPrice = pricedItems.length > 0 
    ? pricedItems.reduce((sum, i) => sum + (i.price || 0), 0) / pricedItems.length 
    : 0;

  if (loading) return <Container sx={{ p: 4 }}><LinearProgress /></Container>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <AttachMoneyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Pricing Management
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddNew}>
          Add Product/Service
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Add your products and services with prices. The AI will use these prices when customers ask about costs.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3">{totalItems}</Typography>
              <Typography variant="body2">Total Items</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3">${avgPrice.toFixed(2)}</Typography>
              <Typography variant="body2">Average Price</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'warning.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3">{items.filter(i => i.available).length}</Typography>
              <Typography variant="body2">Available</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Filter by Category</InputLabel>
          <Select
            value={categoryFilter}
            label="Filter by Category"
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <MenuItem value="">All Categories</MenuItem>
            {CATEGORIES.map(cat => (
              <MenuItem key={cat} value={cat}>{cat}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredItems.map((item) => (
              <TableRow key={item.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{item.name}</TableCell>
                <TableCell><Chip label={item.category} size="small" /></TableCell>
                <TableCell>{item.description || '-'}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  {item.price ? `$${item.price.toFixed(2)}` : '-'}
                </TableCell>
                <TableCell align="center">
                  <Chip 
                    label={item.available ? 'Available' : 'Unavailable'} 
                    size="small" 
                    color={item.available ? 'success' : 'error'} 
                  />
                </TableCell>
                <TableCell align="center">
                  <IconButton size="small" onClick={() => handleEdit(item)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" color="error" onClick={() => handleDelete(item.id!)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {filteredItems.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No pricing items yet. Click "Add Product/Service" to get started!
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Product/Service' : 'Add Product/Service'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="e.g., Kung Pow Chicken, Haircut, Legal Consultation"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Price"
                type="number"
                InputProps={{ startAdornment: '$' }}
                value={formData.price || ''}
                onChange={(e) => setFormData({ ...formData, price: e.target.value ? parseFloat(e.target.value) : null })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
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
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the product/service"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.available}
                    onChange={(e) => setFormData({ ...formData, available: e.target.checked })}
                  />
                }
                label="Available for ordering/booking"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={saving || !formData.name}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
