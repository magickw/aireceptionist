import * as React from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface AnalyticsData {
  totalCalls: number;
  avgCallDuration: number;
  appointmentsBooked: number;
}

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [businessId, setBusinessId] = useState<number | null>(null);

  useEffect(() => {
    const fetchBusinessAndAnalytics = async () => {
      try {
        // Fetch the first business (assuming for now, will be dynamic later)
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const fetchedBusinessId = businessResponse.data[0].id;
          setBusinessId(fetchedBusinessId);

          // Fetch analytics for that business
          const analyticsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics/business/${fetchedBusinessId}`);
          setAnalyticsData(analyticsResponse.data);
        }
      } catch (error) {
        console.error('Error fetching analytics data:', error);
      }
    };
    fetchBusinessAndAnalytics();
  }, []);

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Call Analytics
        </Typography>
        {analyticsData ? (
          <Box>
            <Typography variant="h6">Total Calls: {analyticsData.totalCalls}</Typography>
            <Typography variant="h6">Appointments Booked: {analyticsData.appointmentsBooked}</Typography>
            {/* Add more analytics data here */}
          </Box>
        ) : (
          <Typography>Loading analytics data...</Typography>
        )}
      </Box>
    </Container>
  );
}
