'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, LinearProgress, Button, Tooltip, Dialog,
  DialogTitle, DialogContent, DialogActions, Avatar, Alert
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import HistoryIcon from '@mui/icons-material/History';
import PsychologyIcon from '@mui/icons-material/Psychology';
import InfoIcon from '@mui/icons-material/Info';
import RefreshIcon from '@mui/icons-material/Refresh';
import api from '@/services/api';

interface ApprovalRequest {
  id: number;
  request_type: string;
  status: string;
  reason: string;
  original_response: string;
  final_response: string | null;
  call_session_id: string;
  created_at: string;
  reviewed_at: string | null;
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [msg, setMsg] = useState({ text: '', type: 'success' as 'success' | 'error' | 'info' });

  useEffect(() => {
    fetchApprovals();
  }, []);

  const fetchApprovals = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/approvals/history');
      setApprovals(response.data || []);
    } catch (error) {
      console.error('Failed to fetch approvals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTrainAI = async (approval: ApprovalRequest) => {
    try {
      await api.post(`/ai-training/convert-approval/${approval.id}`);
      setMsg({ text: 'Successfully added to AI training scenarios!', type: 'success' });
    } catch (error) {
      console.error('Failed to convert to training:', error);
      setMsg({ text: 'Failed to add training scenario. Ensure the approval is reviewed.', type: 'error' });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return 'warning';
      case 'approved': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  if (isLoading) {
    return <Container sx={{ mt: 4 }}><LinearProgress /></Container>;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">AI Approvals & Feedback</Typography>
        <Button startIcon={<RefreshIcon />} onClick={fetchApprovals} variant="outlined">Refresh</Button>
      </Box>

      {msg.text && (
        <Alert severity={msg.type} sx={{ mb: 3 }} onClose={() => setMsg({ text: '', type: 'info' })}>
          {msg.text}
        </Alert>
      )}

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead sx={{ bgcolor: '#f8fafc' }}>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Reason for Review</TableCell>
              <TableCell>Session ID</TableCell>
              <TableCell>Requested</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {approvals.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No approval requests found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              approvals.map((approval) => (
                <TableRow key={approval.id} hover>
                  <TableCell>
                    <Chip
                      label={approval.status.toUpperCase()}
                      size="small"
                      color={getStatusColor(approval.status) as any}
                    />
                  </TableCell>
                  <TableCell><Typography variant="body2" fontWeight="medium">{approval.request_type}</Typography></TableCell>
                  <TableCell><Typography variant="body2">{approval.reason}</Typography></TableCell>
                  <TableCell><Typography variant="caption" sx={{ fontFamily: 'monospace' }}>{approval.call_session_id.substring(0, 8)}...</Typography></TableCell>
                  <TableCell><Typography variant="body2">{formatDateTime(approval.created_at)}</Typography></TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                      <Tooltip title="View Details">
                        <IconButton size="small" onClick={() => { setSelectedApproval(approval); setDetailsOpen(true); }}>
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {approval.status === 'approved' && (
                        <Tooltip title="Train AI from this feedback">
                          <IconButton 
                            size="small" 
                            color="primary" 
                            onClick={() => handleTrainAI(approval)}
                          >
                            <PsychologyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Approval Request Details</DialogTitle>
        <DialogContent>
          {selectedApproval && (
            <Box sx={{ pt: 1 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="overline" color="text.secondary">Original AI Response</Typography>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: '#fff7ed', mt: 1 }}>
                    <Typography variant="body2">{selectedApproval.original_response || 'No original response recorded'}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="overline" color="text.secondary">Manager Final Response</Typography>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f0fdf4', mt: 1 }}>
                    <Typography variant="body2">{selectedApproval.final_response || 'Pending review'}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="overline" color="text.secondary">Context & Reasoning</Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>{selectedApproval.reason}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="overline" color="text.secondary">Requested At</Typography>
                  <Typography variant="body2">{formatDateTime(selectedApproval.created_at)}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="overline" color="text.secondary">Reviewed At</Typography>
                  <Typography variant="body2">{formatDateTime(selectedApproval.reviewed_at)}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="overline" color="text.secondary">Status</Typography>
                  <Box sx={{ mt: 0.5 }}><Chip label={selectedApproval.status} size="small" color={getStatusColor(selectedApproval.status) as any} /></Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          {selectedApproval?.status === 'approved' && (
            <Button 
              startIcon={<PsychologyIcon />} 
              variant="contained" 
              onClick={() => { handleTrainAI(selectedApproval); setDetailsOpen(false); }}
            >
              Add to AI Training
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
}
