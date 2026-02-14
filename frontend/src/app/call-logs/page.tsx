'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, LinearProgress } from '@mui/material';
import api from '@/services/api';

export default function CallLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const businessRes = await api.get('/businesses');
        if (businessRes.data.length > 0) {
          const businessId = businessRes.data[0].id;
          const logsRes = await api.get(`/call-logs/?business_id=${businessId}`);
          setLogs(logsRes.data);
        }
      } catch (error) { console.error('Failed to fetch call logs', error); }
      finally { setLoading(false); }
    };
    fetchData();
  }, []);

  if (loading) return <Container sx={{p:4}}><LinearProgress/></Container>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Call Logs</Typography>
      <TableContainer component={Paper}><Table><TableHead><TableRow><TableCell>Customer</TableCell><TableCell>Duration</TableCell><TableCell>Date</TableCell><TableCell>Summary</TableCell></TableRow></TableHead>
      <TableBody>
        {logs.map((log) => (
          <TableRow key={log.id}>
            <TableCell>{log.customer_phone}</TableCell>
            <TableCell>{log.duration_seconds}s</TableCell>
            <TableCell>{new Date(log.started_at).toLocaleString()}</TableCell>
            <TableCell>{log.summary}</TableCell>
          </TableRow>
        ))}
      </TableBody></Table></TableContainer>
    </Container>
  );
}
