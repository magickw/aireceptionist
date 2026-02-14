'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Grid,
  CircularProgress, TextField, Button, Alert
} from '@mui/material';
import { SentimentSatisfied, SentimentDissatisfied, SentimentNeutral } from '@mui/icons-material';
import { sentimentApi } from '@/services/api';

export default function SentimentPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [analyzeText, setAnalyzeText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => { fetchStats(); }, []);

  const fetchStats = async () => {
    try {
      const res = await sentimentApi.getBusiness(30);
      setStats(res.data);
    } catch (error) { console.error('Failed to fetch stats', error); }
    finally { setLoading(false); }
  };

  const handleAnalyze = async () => {
    if (!analyzeText) return;
    setAnalyzing(true);
    try {
      const res = await sentimentApi.analyze(analyzeText);
      setResult(res.data);
    } catch (error) { console.error('Failed to analyze', error); }
    finally { setAnalyzing(false); }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return <SentimentSatisfied color="success" />;
      case 'negative': return <SentimentDissatisfied color="error" />;
      default: return <SentimentNeutral />;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Sentiment Analysis</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Analyze customer sentiment from call conversations.
      </Typography>

      {loading ? <CircularProgress /> : stats && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Positive</Typography>
                  <Typography variant="h3" color="success.main">
                    {stats.sentiment_distribution?.positive?.percentage}%
                  </Typography>
                  <Typography>{stats.sentiment_distribution?.positive?.count} calls</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Neutral</Typography>
                  <Typography variant="h3">
                    {stats.sentiment_distribution?.neutral?.percentage}%
                  </Typography>
                  <Typography>{stats.sentiment_distribution?.neutral?.count} calls</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Negative</Typography>
                  <Typography variant="h3" color="error.main">
                    {stats.sentiment_distribution?.negative?.percentage}%
                  </Typography>
                  <Typography>{stats.sentiment_distribution?.negative?.count} calls</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}

      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Analyze Text</Typography>
          <TextField fullWidth multiline rows={3} placeholder="Enter text to analyze..." 
            value={analyzeText} onChange={(e) => setAnalyzeText(e.target.value)} sx={{ mb: 2 }} />
          <Button variant="contained" onClick={handleAnalyze} disabled={analyzing || !analyzeText}>
            {analyzing ? <CircularProgress size={20} /> : 'Analyze'}
          </Button>

          {result && (
            <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                {getSentimentIcon(result.sentiment)}
                <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>{result.sentiment}</Typography>
                <Typography>Score: {result.score}</Typography>
              </Box>
              {result.keywords?.positive?.length > 0 && (
                <Alert severity="success" sx={{ mb: 1 }}>
                  Positive: {result.keywords.positive.join(', ')}
                </Alert>
              )}
              {result.keywords?.negative?.length > 0 && (
                <Alert severity="error">
                  Negative: {result.keywords.negative.join(', ')}
                </Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
}
