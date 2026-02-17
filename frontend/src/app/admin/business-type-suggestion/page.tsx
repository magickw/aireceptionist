"use client";

import { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  Chip,
  CircularProgress,
  LinearProgress,
  Paper,
} from '@mui/material';
import { Sparkles, Lightbulb, Error as ErrorIcon, Star, StarBorder } from '@mui/icons-material';

interface BusinessTypeSuggestion {
  business_type: string;
  confidence: number;
  name: string;
  icon: string;
}

export default function BusinessTypeSuggestionPage() {
  const [description, setDescription] = useState('');
  const [suggestions, setSuggestions] = useState<BusinessTypeSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSuggest = async () => {
    if (!description.trim()) {
      setError('Please enter a business description');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('/api/v1/admin/templates/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, top_n: 5 }),
      });

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data);
      } else {
        setError('Failed to get suggestions');
      }
    } catch (err) {
      setError('An error occurred while fetching suggestions');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.5) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      <Box mb={6}>
        <Typography variant="h3" gutterBottom display="flex" alignItems="center" gap={2}>
          <Sparkles fontSize="large" />
          Business Type Suggestion
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Use AI to suggest the most appropriate business type based on your description
        </Typography>
      </Box>

      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ pt: 4 }}>
          <Box mb={4}>
            <Typography variant="h6" gutterBottom>
              Describe Your Business
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Enter a detailed description of your business to get AI-powered type suggestions
            </Typography>
          </Box>
          
          <TextField
            fullWidth
            multiline
            rows={6}
            label="Business Description"
            placeholder="e.g., A restaurant serving Italian cuisine with pasta, pizza, and wine. We offer dine-in, takeout, and delivery services..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            sx={{ mb: 3 }}
          />
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleSuggest}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <Lightbulb />}
          >
            {loading ? 'Analyzing...' : 'Get Suggestions'}
          </Button>
        </CardContent>
      </Card>

      {suggestions.length > 0 && (
        <Box>
          <Typography variant="h5" gutterBottom>
            Suggested Business Types
          </Typography>
          {suggestions.map((suggestion, index) => (
            <Card
              key={suggestion.business_type}
              sx={{
                mb: 2,
                border: index === 0 ? '2px solid' : '1px solid',
                borderColor: index === 0 ? 'primary.main' : 'divider',
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box display="flex" alignItems="flex-start" gap={3}>
                    <Paper
                      sx={{
                        p: 2,
                        bgcolor: 'primary.10',
                        borderRadius: 2,
                      }}
                    >
                      <Typography variant="h3">{suggestion.icon}</Typography>
                    </Paper>
                    <Box>
                      <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                        <Typography variant="h6">{suggestion.name}</Typography>
                        {index === 0 && (
                          <Chip
                            label="Best Match"
                            color="primary"
                            size="small"
                          />
                        )}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Business Type: <code>{suggestion.business_type}</code>
                      </Typography>
                    </Box>
                  </Box>
                  <Box textAlign="right">
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      Confidence
                    </Typography>
                    <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                      <Chip
                        label={getConfidenceLabel(suggestion.confidence)}
                        color={getConfidenceColor(suggestion.confidence) as any}
                        size="small"
                      />
                      <Typography variant="h4" fontWeight="bold">
                        {Math.round(suggestion.confidence * 100)}%
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                
                <LinearProgress
                  variant="determinate"
                  value={suggestion.confidence * 100}
                  color={getConfidenceColor(suggestion.confidence) as any}
                  sx={{ mt: 3, height: 8, borderRadius: 1 }}
                />
              </CardContent>
            </Card>
          ))}
          
          {suggestions.length > 0 && suggestions[0].confidence < 0.5 && (
            <Alert severity="warning" sx={{ mt: 3 }}>
              <Box>
                <Typography variant="subtitle2" fontWeight="bold">
                  Low Confidence Results
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  The AI couldn't confidently determine your business type. This might be because:
                </Typography>
                <Box component="ul" sx={{ mt: 2, mb: 0 }}>
                  <li>Your description is too vague or brief</li>
                  <li>Your business type might not be in our system yet</li>
                  <li>You may be describing a unique business model</li>
                </Box>
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Consider providing more details about your services, products, and business operations.
                </Typography>
              </Box>
            </Alert>
          )}
        </Box>
      )}

      {description && !loading && suggestions.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Lightbulb sx={{ fontSize: 48, opacity: 0.5, mb: 2 }} />
            <Typography variant="body1" color="text.secondary">
              Enter a business description above and click "Get Suggestions" to see AI-powered recommendations.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Container>
  );
}