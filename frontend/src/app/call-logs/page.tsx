'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, LinearProgress, TextField, InputAdornment,
  FormControl, InputLabel, Select, MenuItem, Dialog, DialogTitle,
  DialogContent, DialogActions, Button, Avatar, Tooltip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import PhoneIcon from '@mui/icons-material/Phone';
import InfoIcon from '@mui/icons-material/Info';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import SentimentNeutralIcon from '@mui/icons-material/SentimentNeutral';
import api from '@/services/api';

interface CallSession {
  id: string;
  business_id: number;
  customer_phone: string | null;
  customer_name: string | null;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  ai_confidence: number | null;
  summary: string | null;
  sentiment: string | null;
  recording_url: string | null;
  voicemail_detected: boolean | null;
  created_at: string;
}

interface CallStats {
  total: number;
  active: number;
  ended: number;
  missed: number;
  avgDuration: number;
  avgConfidence: number;
}

export default function CallLogsPage() {
  const [calls, setCalls] = useState<CallSession[]>([]);
  const [filteredCalls, setFilteredCalls] = useState<CallSession[]>([]);
  const [stats, setStats] = useState<CallStats>({
    total: 0, active: 0, ended: 0, missed: 0, avgDuration: 0, avgConfidence: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCall, setSelectedCall] = useState<CallSession | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [isTrainingOpen, setIsTrainingOpen] = useState(false);
  const [trainingInput, setTrainingInput] = useState('');
  const [trainingResponse, setTrainingResponse] = useState('');
  const [trainingCategory, setTrainingCategory] = useState('general_inquiry');
  const [isSubmittingTraining, setIsSubmittingTraining] = useState(false);

  useEffect(() => {
    fetchCalls();
  }, []);

  const handleTrainAI = (call: CallSession) => {
    setSelectedCall(call);
    setTrainingInput(call.summary || '');
    setTrainingResponse('');
    setIsTrainingOpen(true);
  };

  const submitTraining = async () => {
    if (!selectedCall) return;
    setIsSubmittingTraining(true);
    try {
      await api.post(`/ai-training/convert-call-log/${selectedCall.id}`, {
        user_input: trainingInput,
        expected_response: trainingResponse,
        category: trainingCategory
      });
      alert('Successfully added to AI training scenarios!');
      setIsTrainingOpen(false);
    } catch (error) {
      console.error('Failed to submit training:', error);
      alert('Failed to add training scenario.');
    } finally {
      setIsSubmittingTraining(false);
    }
  };

  useEffect(() => {
    filterCalls();
  }, [calls, searchQuery, statusFilter]);

  const fetchCalls = async () => {
    setIsLoading(true);
    try {
      const businessRes = await api.get('/businesses');
      if (businessRes.data.length > 0) {
        const businessId = businessRes.data[0].id;
        const response = await api.get(`/call-logs/?business_id=${businessId}`);
        const callData = response.data || [];
        setCalls(callData);
        
        // Calculate stats
        const total = callData.length;
        const active = callData.filter((c: CallSession) => c.status === 'active').length;
        const ended = callData.filter((c: CallSession) => c.status === 'ended').length;
        const missed = callData.filter((c: CallSession) => c.status === 'missed' || c.voicemail_detected).length;
        
        const callsWithDuration = callData.filter((c: CallSession) => c.duration_seconds);
        const avgDuration = callsWithDuration.length > 0
          ? callsWithDuration.reduce((sum: number, c: CallSession) => sum + (c.duration_seconds || 0), 0) / callsWithDuration.length
          : 0;
        
        const callsWithConfidence = callData.filter((c: CallSession) => c.ai_confidence);
        const avgConfidence = callsWithConfidence.length > 0
          ? callsWithConfidence.reduce((sum: number, c: CallSession) => sum + Number(c.ai_confidence || 0), 0) / callsWithConfidence.length
          : 0;
        
        setStats({
          total, active, ended, missed,
          avgDuration: Math.round(avgDuration),
          avgConfidence: Math.round(avgConfidence * 100)
        });
      }
    } catch (error) {
      console.error('Failed to fetch calls:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterCalls = () => {
    let filtered = [...calls];
    if (statusFilter !== 'all') {
      filtered = filtered.filter(c => c.status === statusFilter);
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(c =>
        (c.customer_phone && c.customer_phone.toLowerCase().includes(query)) ||
        (c.customer_name && c.customer_name.toLowerCase().includes(query)) ||
        (c.summary && c.summary.toLowerCase().includes(query))
      );
    }
    setFilteredCalls(filtered);
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'ended': return 'default';
      case 'missed': return 'error';
      case 'transferred': return 'warning';
      default: return 'default';
    }
  };

  const getSentimentIcon = (sentiment: string | null) => {
    if (!sentiment) return <SentimentNeutralIcon color="disabled" fontSize="small" />;
    switch (sentiment.toLowerCase()) {
      case 'positive': return <SentimentSatisfiedIcon color="success" fontSize="small" />;
      case 'negative': return <SentimentDissatisfiedIcon color="error" fontSize="small" />;
      default: return <SentimentNeutralIcon color="info" fontSize="small" />;
    }
  };

  if (isLoading) {
    return <Container sx={{ mt: 4 }}><LinearProgress /></Container>;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">Call Logs</Typography>
        <Button startIcon={<RefreshIcon />} onClick={fetchCalls} variant="outlined">Refresh</Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={4} md={2}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight="bold" color="primary">{stats.total}</Typography>
            <Typography variant="body2" color="text.secondary">Total Calls</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight="bold" color="success.main">{stats.active}</Typography>
            <Typography variant="body2" color="text.secondary">Active</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight="bold">{stats.ended}</Typography>
            <Typography variant="body2" color="text.secondary">Completed</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight="bold" color="error.main">{stats.missed}</Typography>
            <Typography variant="body2" color="text.secondary">Missed</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight="bold">{formatDuration(stats.avgDuration)}</Typography>
            <Typography variant="body2" color="text.secondary">Avg Duration</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight="bold" color="secondary.main">{stats.avgConfidence}%</Typography>
            <Typography variant="body2" color="text.secondary">AI Confidence</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          placeholder="Search by phone, name, or summary..."
          size="small"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
          sx={{ flexGrow: 1, maxWidth: 400 }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select value={statusFilter} label="Status" onChange={(e) => setStatusFilter(e.target.value)}>
            <MenuItem value="all">All Statuses</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="ended">Ended</MenuItem>
            <MenuItem value="missed">Missed</MenuItem>
            <MenuItem value="transferred">Transferred</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Calls Table */}
      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead sx={{ bgcolor: '#f8fafc' }}>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>AI Confidence</TableCell>
              <TableCell>Sentiment</TableCell>
              <TableCell>Summary</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCalls.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    {calls.length === 0 ? 'No calls recorded yet' : 'No calls match your filters'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredCalls.map((call) => (
                <TableRow key={call.id} hover>
                  <TableCell>
                    <Chip
                      label={call.status.toUpperCase()}
                      size="small"
                      color={getStatusColor(call.status) as any}
                      icon={call.status === 'active' ? <PlayArrowIcon /> : <StopIcon />}
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.light' }}><PhoneIcon fontSize="small" /></Avatar>
                      <Box>
                        <Typography variant="body2">{call.customer_phone || 'Unknown'}</Typography>
                        {call.customer_name && <Typography variant="caption" color="text.secondary">{call.customer_name}</Typography>}
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell><Typography variant="body2">{formatDateTime(call.started_at)}</Typography></TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AccessTimeIcon fontSize="small" color="action" />
                      {formatDuration(call.duration_seconds)}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {call.ai_confidence ? (
                      <Chip label={`${Math.round(Number(call.ai_confidence) * 100)}%`} size="small" color={Number(call.ai_confidence) >= 0.85 ? 'success' : 'warning'} variant="outlined" />
                    ) : '-'}
                  </TableCell>
                  <TableCell><Tooltip title={call.sentiment || 'Unknown'}>{getSentimentIcon(call.sentiment)}</Tooltip></TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {call.summary || (call.voicemail_detected ? 'Voicemail detected' : '-')}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => { setSelectedCall(call); setDetailsOpen(true); }}>
                        <InfoIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Train AI from this Call">
                      <IconButton size="small" color="primary" onClick={() => { setSelectedCall(call); setTrainingInput(call.summary || ''); setIsTrainingOpen(true); }}>
                        <PhoneIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Call Details</DialogTitle>
        <DialogContent>
          {selectedCall && (
            <Box sx={{ pt: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Call ID</Typography><Typography variant="body2">{selectedCall.id}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Status</Typography><Typography variant="body2">{selectedCall.status}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Customer Phone</Typography><Typography variant="body2">{selectedCall.customer_phone || 'Unknown'}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Customer Name</Typography><Typography variant="body2">{selectedCall.customer_name || 'Unknown'}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Started At</Typography><Typography variant="body2">{formatDateTime(selectedCall.started_at)}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Ended At</Typography><Typography variant="body2">{formatDateTime(selectedCall.ended_at)}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Duration</Typography><Typography variant="body2">{formatDuration(selectedCall.duration_seconds)}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">AI Confidence</Typography><Typography variant="body2">{selectedCall.ai_confidence ? `${Math.round(Number(selectedCall.ai_confidence) * 100)}%` : 'N/A'}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Sentiment</Typography><Typography variant="body2">{selectedCall.sentiment || 'Unknown'}</Typography></Grid>
                <Grid item xs={6}><Typography variant="overline" color="text.secondary">Voicemail</Typography><Typography variant="body2">{selectedCall.voicemail_detected ? 'Yes' : 'No'}</Typography></Grid>
                <Grid item xs={12}><Typography variant="overline" color="text.secondary">Summary</Typography><Typography variant="body2">{selectedCall.summary || 'No summary available'}</Typography></Grid>
                {selectedCall.recording_url && (
                  <Grid item xs={12}><Typography variant="overline" color="text.secondary">Recording</Typography><Box sx={{ mt: 1 }}><audio controls src={selectedCall.recording_url} style={{ width: '100%' }} /></Box></Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setDetailsOpen(false)}>Close</Button></DialogActions>
      </Dialog>

      {/* AI Training Dialog */}
      <Dialog open={isTrainingOpen} onClose={() => setIsTrainingOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Convert Call Log to AI Training Scenario</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Correcting the AI's response here will help the model handle similar queries more effectively in the future.
            </Typography>
            
            <TextField
              label="Customer Input (from call)"
              multiline
              rows={3}
              fullWidth
              value={trainingInput}
              onChange={(e) => setTrainingInput(e.target.value)}
              placeholder="What did the customer say?"
              helperText="The user query that triggered this correction"
            />
            
            <TextField
              label="Expected AI Response (your correction)"
              multiline
              rows={4}
              fullWidth
              value={trainingResponse}
              onChange={(e) => setTrainingResponse(e.target.value)}
              placeholder="What SHOULD the AI have said?"
              color="success"
              focused
              helperText="The ideal response you want the AI to provide"
            />

            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={trainingCategory}
                label="Category"
                onChange={(e) => setTrainingCategory(e.target.value)}
              >
                <MenuItem value="appointment_booking">Appointment Booking</MenuItem>
                <MenuItem value="customer_support">Customer Support</MenuItem>
                <MenuItem value="sales_inquiry">Sales Inquiry</MenuItem>
                <MenuItem value="complaint_handling">Complaint Handling</MenuItem>
                <MenuItem value="general_inquiry">General Inquiry</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsTrainingOpen(false)} disabled={isSubmittingTraining}>Cancel</Button>
          <Button 
            onClick={submitTraining} 
            variant="contained" 
            color="success" 
            disabled={!trainingInput || !trainingResponse || isSubmittingTraining}
          >
            {isSubmittingTraining ? 'Saving...' : 'Add to Training'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}