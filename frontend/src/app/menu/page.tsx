'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, TextField, Button, Card, CardContent, LinearProgress, 
  Grid, Chip, IconButton, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Switch, FormControlLabel, Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import api from '@/services/api';

interface MenuItem {
  id?: number;
  name: string;
  description: string;
  price: number | null;
  category: string;
  available: boolean;
  dietary_info: { vegetarian?: boolean; vegan?: boolean; gluten_free?: boolean };
  is_active: boolean;
}

const CATEGORIES = [
  'Appetizers', 'Main Course', 'Desserts', 'Drinks', 
  'Breakfast', 'Lunch', 'Dinner', 'Sides', 'Specials', 'Other'
];

export default function MenuManagementPage() {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('');

  const emptyItem: MenuItem = {
    name: '',
    description: '',
    price: null,
    category: 'Main Course',
    available: true,
    dietary_info: { vegetarian: false, vegan: false, gluten_free: false },
    is_active: true
  };

  const [formData, setFormData] = useState<MenuItem>(emptyItem);

  useEffect(() => {
    fetchMenuItems();
  }, []);

  const fetchMenuItems = async () => {
    try {
      const res = await api.get('/menu/', { params: { business_id: 1 } });
      setMenuItems(res.data);
    } catch (error) {
      console.error('Failed to fetch menu items', error);
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
      fetchMenuItems();
      setFormData(emptyItem);
      setEditingItem(null);
    } catch (error) {
      console.error('Failed to save menu item', error);
      alert('Failed to save menu item.');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item: MenuItem) => {
    setEditingItem(item);
    setFormData(item);
    setDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this item?')) return;
    try {
      await api.delete(`/menu/${id}`, { params: { business_id: 1 } });
      fetchMenuItems();
    } catch (error) {
      console.error('Failed to delete menu item', error);
    }
  };

  const handleAddNew = () => {
    setEditingItem(null);
    setFormData(emptyItem);
    setDialogOpen(true);
  };

  const filteredItems = categoryFilter 
    ? menuItems.filter(item => item.category === categoryFilter)
    : menuItems;

  const groupedItems = filteredItems.reduce((acc, item) => {
    const cat = item.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {} as Record<string, MenuItem[]>);

  if (loading) return <Container sx={{ p: 4 }}><LinearProgress /></Container>;

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <RestaurantIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Menu Management
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddNew}>
          Add Menu Item
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Add your menu items here so the AI receptionist can help customers with orders and answer pricing questions.
      </Alert>

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

      {Object.entries(groupedItems).map(([category, items]) => (
        <Card key={category} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
              {category}
            </Typography>
            <Grid container spacing={2}>
              {items.map((item) => (
                <Grid item xs={12} sm={6} key={item.id}>
                  <Card variant="outlined" sx={{ p: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {item.name}
                          {!item.available && <Chip label="Unavailable" size="small" color="error" sx={{ ml: 1 }} />}
                        </Typography>
                        {item.description && (
                          <Typography variant="body2" color="text.secondary">
                            {item.description}
                          </Typography>
                        )}
                        <Typography variant="h6" color="primary" sx={{ mt: 1 }}>
                          {item.price ? `$${item.price.toFixed(2)}` : 'Price TBD'}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          {item.dietary_info?.vegetarian && <Chip label="Vegetarian" size="small" sx={{ mr: 0.5 }} />}
                          {item.dietary_info?.vegan && <Chip label="Vegan" size="small" sx={{ mr: 0.5 }} />}
                          {item.dietary_info?.gluten_free && <Chip label="Gluten-Free" size="small" />}
                        </Box>
                      </Box>
                      <Box>
                        <IconButton size="small" onClick={() => handleEdit(item)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDelete(item.id!)}>
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </Box>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      ))}

      {filteredItems.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="text.secondary">
              No menu items yet. Click "Add Menu Item" to get started!
            </Typography>
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Menu Item' : 'Add Menu Item'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Item Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Price"
                type="number"
                InputProps={{ startAdornment: '$' }}
                value={formData.price || ''}
                onChange={(e) => setFormData({ ...formData, price: e.target.value ? parseFloat(e.target.value) : null })}
              />
            </Grid>
            <Grid item xs={6}>
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
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.available}
                    onChange={(e) => setFormData({ ...formData, available: e.target.checked })}
                  />
                }
                label="Available"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Dietary Information</Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.dietary_info?.vegetarian || false}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      dietary_info: { ...formData.dietary_info, vegetarian: e.target.checked } 
                    })}
                  />
                }
                label="Vegetarian"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.dietary_info?.vegan || false}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      dietary_info: { ...formData.dietary_info, vegan: e.target.checked } 
                    })}
                  />
                }
                label="Vegan"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.dietary_info?.gluten_free || false}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      dietary_info: { ...formData.dietary_info, gluten_free: e.target.checked } 
                    })}
                  />
                }
                label="Gluten-Free"
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
