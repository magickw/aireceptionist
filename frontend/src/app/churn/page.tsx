'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Grid,
  CircularProgress, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, Alert, TextField, Button
} from '@mui/material';
import { Warning, TrendingDown } from '@mui/icons-material';
import { churnApi } from '@/services/api';

export default function ChurnPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [atRisk, setAtRisk] = useState<any[]>([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [statsRes, atRiskRes] = await Promise.all([
        churnApi.getStats(),
        churnApi.getAtRisk(40)
      ]);
      setStats(statsRes.data);
      setAtRisk(atRiskRes.data.at_risk_customers || []);
    } catch (error) { console.error('Failed to fetch data', error); }
    finally { setLoading(false); }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      default: return 'success';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Customer Churn Prediction</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Identify customers at risk of churning based on call patterns.
      </Typography>

      {loading ? <CircularProgress /> : stats && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="primary">At Risk</Typography>
                  <Typography variant="h3">{stats.total_at_risk}</Typography>
                  <Typography>customers</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="error">High Risk</Typography>
                  <Typography variant="h3" color="error.main">{stats.distribution?.high}</Typography>
                  <Typography>{stats.percentages?.high}%</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="warning">Medium Risk</Typography>
                  <Typography variant="h3" color="warning.main">{stats.distribution?.medium}</Typography>
                  <Typography>{stats.percentages?.medium}%</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Typography variant="h5" sx={{ mb: 2 }}>At-Risk Customers</Typography>
          {atRisk.length === 0 ? (
            <Alert severity="success">No at-risk customers found!</Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Phone</TableCell>
                    <TableCell>Risk Score</TableCell>
                    <TableCell>Risk Level</TableCell>
                    <TableCell>Last Call</TableCell>
                    <TableCell>Factors</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {atRisk.map((customer, i) => (
                    <TableRow key={i}>
                      <TableCell>{customer.customer_phone}</TableCell>
                      <TableCell><Typography variant="h6">{customer.risk_score}</Typography></TableCell>
                      <TableCell>
                        <Chip label={customer.risk_level} color={getRiskColor(customer.risk_level)} size="small" />
                      </TableCell>
                      <TableCell>{customer.last_call ? new Date(customer.last_call).toLocaleDateString() : 'Never'}</TableCell>
                      <TableCell>
                        {customer.factors?.map((f: any, j: number) => (
                          <Chip key={j} label={f.factor} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                        ))}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}
    </Container>
  );
}
