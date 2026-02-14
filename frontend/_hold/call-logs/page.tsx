'use client';
import * as React from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface CallLog {
  id: number;
  business_id: number;
  customer_phone: string;
  call_sid: string;
  transcript: string;
  created_at: string;
  recording_url?: string; // Make it optional as it might not always be present
}

export default function CallLogsPage() {
  const [callLogs, setCallLogs] = useState<CallLog[]>([]);
  const [businessId, setBusinessId] = useState<number | null>(null);

  useEffect(() => {
    const fetchBusinessAndCallLogs = async () => {
      try {
        // Fetch the first business (assuming for now, will be dynamic later)
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const fetchedBusinessId = businessResponse.data[0].id;
          setBusinessId(fetchedBusinessId);

          // Fetch call logs for that business
          const callLogsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/call-logs/business/${fetchedBusinessId}`);
          setCallLogs(callLogsResponse.data);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };
    fetchBusinessAndCallLogs();
  }, []);

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Call Logs
        </Typography>
        {callLogs.length === 0 ? (
          <Typography>No call logs found.</Typography>
        ) : (
          <List>
            {callLogs.map((log) => (
              <ListItem key={log.id} divider>
                <ListItemText
                  primary={`Call from: ${log.customer_phone} on ${new Date(log.created_at).toLocaleString()}`}
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="text.primary">
                        {log.transcript || 'No transcript available.'}
                      </Typography>
                      {log.recording_url && (
                        <Box component="span" sx={{ display: 'block', mt: 1 }}>
                          <a href={log.recording_url} target="_blank" rel="noopener noreferrer">
                            Listen to Recording
                          </a>
                        </Box>
                      )}
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Container>
  );
}
