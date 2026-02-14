'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Alert, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions,
  Grid, Switch, FormControlLabel
} from '@mui/material';
import { Call, Add, Delete } from '@mui/icons-material';
import { callRoutingApi } from '@/services/api';

export default function CallRoutingPage() {
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState<any[]>([]);
  const [options, setOptions] = useState<any>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', conditions: {} as any, action: '', action_value: '' });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [rulesRes, optionsRes] = await Promise.all([
        callRoutingApi.list(),
        callRoutingApi.getOptions()
      ]);
      setRules(rulesRes.data.rules || []);
      setOptions(optionsRes.data);
    } catch (error) { console.error('Failed to fetch', error); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.action) return;
    try {
      await callRoutingApi.create(formData);
      setDialogOpen(false);
      setFormData({ name: '', conditions: {}, action: '', action_value: '' });
      fetchData();
    } catch (error) { alert('Failed to create'); }
  };

  const handleToggle = async (ruleId: number, isActive: boolean) => {
    try {
      await callRoutingApi.update(ruleId, { is_active: !isActive });
      fetchData();
    } catch (error) { alert('Failed to update'); }
  };

  const handleDelete = async (ruleId: number) => {
    if (!confirm('Delete this rule?')) return;
    try {
      await callRoutingApi.delete(ruleId);
      fetchData();
    } catch (error) { alert('Failed to delete'); }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Call Routing</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
          Add Rule
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure intelligent call routing based on time, caller ID, and other conditions.
      </Typography>

      {loading ? <CircularProgress /> : rules.length === 0 ? (
        <Alert severity="info">No routing rules configured. Add one to get started!</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Conditions</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell>{rule.name}</TableCell>
                  <TableCell>
                    {Object.entries(rule.conditions || {}).map(([k, v]) => (
                      <Chip key={k} label={`${k}: ${JSON.stringify(v)}`} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </TableCell>
                  <TableCell>{rule.action} → {rule.action_value}</TableCell>
                  <TableCell>{rule.priority}</TableCell>
                  <TableCell>
                    <Switch checked={rule.is_active} onChange={() => handleToggle(rule.id, rule.is_active)} size="small" />
                  </TableCell>
                  <TableCell>
                    <Button color="error" size="small" onClick={() => handleDelete(rule.id)}>Delete</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Routing Rule</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Rule Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} sx={{ mt: 2, mb: 2 }} />
          <TextField fullWidth select SelectProps={{ native: true }} label="Action" value={formData.action}
            onChange={(e) => setFormData({ ...formData, action: e.target.value })} sx={{ mb: 2 }}>
            <option value="">Select action</option>
            {options?.actions?.map((a: string) => <option key={a} value={a}>{a}</option>)}
          </TextField>
          <TextField fullWidth label="Action Value" value={formData.action_value} onChange={(e) => setFormData({ ...formData, action_value: e.target.value })} 
            placeholder="e.g., extension number, phone number" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Create</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
