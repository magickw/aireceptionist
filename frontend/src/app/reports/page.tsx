'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, Grid,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Alert, CircularProgress, ToggleButton, ToggleButtonGroup
} from '@mui/material';
import { Download, Assessment, BarChart, PieChart } from '@mui/icons-material';
import { reportsApi } from '@/services/api';

interface ReportData {
  call_metrics: {
    total_calls: number;
    completed_calls: number;
    missed_calls: number;
    completion_rate: number;
    average_duration_seconds: number;
  };
  customer_metrics: {
    unique_customers: number;
    returning_customers: number;
    new_customers: number;
  };
  hourly_distribution: { hour: number; count: number }[];
}

export default function ReportsPage() {
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState('weekly');
  const [report, setReport] = useState<ReportData | null>(null);

  useEffect(() => { fetchReport(); }, [reportType]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await reportsApi.generateReport(reportType);
      setReport(res.data);
    } catch (error) { console.error('Failed to fetch report', error); }
    finally { setLoading(false); }
  };

  const handleExport = async () => {
    try {
      const res = await reportsApi.exportCSV();
      const blob = new Blob([res.data.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = res.data.filename;
      a.click();
    } catch (error) { alert('Failed to export'); }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Advanced Reports</Typography>
        <Button variant="outlined" startIcon={<Download />} onClick={handleExport}>
          Export CSV
        </Button>
      </Box>

      <Box sx={{ mb: 3 }}>
        <ToggleButtonGroup value={reportType} exclusive onChange={(_, v) => v && setReportType(v)}>
          <ToggleButton value="daily">Daily</ToggleButton>
          <ToggleButton value="weekly">Weekly</ToggleButton>
          <ToggleButton value="monthly">Monthly</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {loading ? <CircularProgress /> : report && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">Total Calls</Typography>
                  <Typography variant="h4">{report.call_metrics.total_calls}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">Completed</Typography>
                  <Typography variant="h4" color="success.main">{report.call_metrics.completed_calls}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">Missed</Typography>
                  <Typography variant="h4" color="error.main">{report.call_metrics.missed_calls}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">Completion Rate</Typography>
                  <Typography variant="h4">{report.call_metrics.completion_rate}%</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Customer Metrics</Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography>Unique Customers: <strong>{report.customer_metrics.unique_customers}</strong></Typography>
                    <Typography>New Customers: <strong>{report.customer_metrics.new_customers}</strong></Typography>
                    <Typography>Returning: <strong>{report.customer_metrics.returning_customers}</strong></Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Hourly Distribution</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {report.hourly_distribution.slice(0, 8).map((h) => (
                            <TableCell key={h.hour} align="center">{h.hour}:00</TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          {report.hourly_distribution.slice(0, 8).map((h) => (
                            <TableCell key={h.hour} align="center">{h.count}</TableCell>
                          ))}
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
}
