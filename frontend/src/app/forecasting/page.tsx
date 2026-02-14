'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Grid, Alert,
  CircularProgress, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, LinearProgress
} from '@mui/material';
import { TrendingUp, AccessTime, CalendarMonth } from '@mui/icons-material';
import { forecastingApi } from '@/services/api';

interface Prediction { date: string; day_of_week: string; predicted_calls: number; confidence: string; }
interface PeakHour { hour: number; count: number; }

export default function ForecastingPage() {
  const [loading, setLoading] = useState(true);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [weeklyData, setWeeklyData] = useState<any>(null);
  const [peakHours, setPeakHours] = useState<PeakHour[]>([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [predRes, weeklyRes, peakRes] = await Promise.all([
        forecastingApi.getPredictions(7),
        forecastingApi.getWeekly(),
        forecastingApi.getPeakHours()
      ]);
      setPredictions(predRes.data.predictions || []);
      setWeeklyData(weeklyRes.data);
      setPeakHours(peakRes.data.peak_hours || []);
    } catch (error) { console.error('Failed to fetch forecast', error); }
    finally { setLoading(false); }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'success';
      case 'medium': return 'warning';
      default: return 'error';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Call Volume Forecasting</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        AI-powered predictions for incoming call volume.
      </Typography>

      {loading ? <CircularProgress /> : (
        <>
          {weeklyData && (
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="primary">Weekly Predicted Total</Typography>
                    <Typography variant="h3">{weeklyData.weekly_total_predicted}</Typography>
                    <Chip 
                      label={`${weeklyData.trend} (${weeklyData.change_percentage > 0 ? '+' : ''}${weeklyData.change_percentage}%)`}
                      color={weeklyData.change_percentage > 0 ? 'success' : weeklyData.change_percentage < 0 ? 'error' : 'default'}
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="primary">Historical Average</Typography>
                    <Typography variant="h3">{weeklyData.historical_weekly_average}</Typography>
                    <Typography variant="body2" color="text.secondary">calls per week</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="primary">Peak Hours</Typography>
                    {peakHours.slice(0, 3).map((p, i) => (
                      <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography>{p.hour}:00</Typography>
                        <Chip label={p.count} size="small" />
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          <Typography variant="h5" sx={{ mb: 2 }}>7-Day Forecast</Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Day</TableCell>
                  <TableCell>Predicted Calls</TableCell>
                  <TableCell>Confidence</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {predictions.map((pred, i) => (
                  <TableRow key={i}>
                    <TableCell>{pred.date}</TableCell>
                    <TableCell>{pred.day_of_week}</TableCell>
                    <TableCell><Typography variant="h6">{pred.predicted_calls}</Typography></TableCell>
                    <TableCell>
                      <Chip label={pred.confidence} color={getConfidenceColor(pred.confidence)} size="small" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Container>
  );
}
