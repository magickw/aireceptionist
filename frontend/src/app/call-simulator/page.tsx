'use client';
import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import LinearProgress from '@mui/material/LinearProgress';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import PhoneIcon from '@mui/icons-material/Phone';
import PhoneDisabledIcon from '@mui/icons-material/PhoneDisabled';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AgentThoughts from '@/components/AgentThoughts';
import AutomationProgress from '@/components/AutomationProgress';
import { ConversationMessage, CallSession } from '@/types/ai';

interface Thought {
  step: string;
  message: string;
  timestamp: Date;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function CallSimulator() {
  const [tabValue, setTabValue] = useState(0);
  const [currentCall, setCurrentCall] = useState<CallSession | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [useContextAware, setUseContextAware] = useState(true);
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [reasoningData, setReasoningData] = useState<any>(null);
  const [automationWorkflow, setAutomationWorkflow] = useState<any>(null);
  const [latencyMetrics, setLatencyMetrics] = useState<any>(null);
  const [callSummaryOpen, setCallSummaryOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickTestScenarios = [
    { emoji: '🍽️', title: 'Book a table', script: "Hi, I'd like to make a reservation for dinner tonight. Table for 2 at 7 PM please." },
    { emoji: '🛍️', title: 'Place an order', script: "I'd like to place an order for delivery. Can I get a Caesar salad and the grilled chicken?" },
    { emoji: '❓', title: 'Ask about hours', script: "What are your business hours? Are you open on weekends?" }
  ];

  const testScenarios = [
    { id: 'booking-basic', title: 'Basic Appointment Booking', description: 'Customer wants to book a simple appointment', starter: "Hi, I'd like to book an appointment for tomorrow.", category: 'Booking' },
    { id: 'business-hours', title: 'Business Hours Inquiry', description: 'Customer asks about operating hours', starter: "What are your business hours?", category: 'Information' }
  ];

  useEffect(() => {
    // Robust WebSocket URL handling with auth token
    let baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    
    // Normalize: remove trailing slash and /api/v1 if already present in base to avoid doubling
    baseUrl = baseUrl.replace(/\/$/, '');
    if (baseUrl.endsWith('/api/v1')) {
      baseUrl = baseUrl.slice(0, -7);
    }
    
    const token = localStorage.getItem("token");
    const wsUrl = `${baseUrl}/api/v1/voice/ws${token ? `?token=${token}` : ''}`;
    
    console.log('🔌 Connecting to WebSocket:', wsUrl.replace(/\?token=.*$/, '?token=REDACTED'));
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'thought') {
          setThoughts(prev => [...prev, { step: data.step, message: data.message, timestamp: new Date() }]);
        } else if (data.type === 'agent_response') {
          setIsProcessing(false);
          addAIMessage(data.text);
          if (data.reasoning) setReasoningData(data.reasoning);
        } else if (data.type === 'latency_metrics') {
          setLatencyMetrics(data.metrics);
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    return () => ws.close();
  }, []);

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const startCall = () => {
    const session: CallSession = {
      id: `call-${Date.now()}`,
      customerPhone: '+1 (555) 123-4567',
      status: 'active',
      startTime: new Date(),
      messages: [],
      context: { customerInfo: {}, intent: 'unknown', businessContext: { businessType: 'general', services: [], operatingHours: {} } }
    };
    setCurrentCall(session);
    setThoughts([]);
    setTimeout(() => addAIMessage("Hello! I'm your AI receptionist. How can I help you today?"), 500);
  };

  const endCall = () => setCurrentCall(null);

  const addAIMessage = (content: string) => {
    const msg: ConversationMessage = { id: `ai-${Date.now()}`, timestamp: new Date(), sender: 'ai', content, type: 'text' };
    setCurrentCall(prev => prev ? { ...prev, messages: [...prev.messages, msg] } : null);
  };

  const sendMessage = () => {
    if (!messageInput.trim() || !wsRef.current) return;
    const msg: ConversationMessage = { id: `u-${Date.now()}`, timestamp: new Date(), sender: 'customer', content: messageInput, type: 'text' };
    setCurrentCall(prev => prev ? { ...prev, messages: [...prev.messages, msg] } : null);
    wsRef.current.send(JSON.stringify({ type: 'user_input', text: messageInput }));
    setMessageInput('');
    setIsProcessing(true);
  };

  const handleQuickScenario = (s: any) => {
    if (!currentCall) startCall();
    setMessageInput(s.script);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 4 }}>AI Call Simulator</Typography>
      
      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="Simulation" />
        <Tab label="Scenarios" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
              <CardHeader 
                avatar={<Avatar sx={{ bgcolor: currentCall ? 'success.main' : 'grey.400' }}><PhoneIcon /></Avatar>}
                title={currentCall ? `Call with ${currentCall.customerPhone}` : "Ready to Start"}
                action={!currentCall ? <Button variant="contained" onClick={startCall}>Start Call</Button> : <Button variant="outlined" color="error" onClick={endCall}>End Call</Button>}
              />
              <CardContent sx={{ flexGrow: 1, overflow: 'auto', bgcolor: '#f8fafc', p: 0 }}>
                {currentCall ? (
                  <List sx={{ p: 2 }}>
                    {currentCall.messages.map((m) => (
                      <ListItem key={m.id} sx={{ flexDirection: 'column', alignItems: m.sender === 'customer' ? 'flex-end' : 'flex-start' }}>
                        <Paper sx={{ p: 2, maxWidth: '80%', bgcolor: m.sender === 'customer' ? 'primary.main' : 'white', color: m.sender === 'customer' ? 'white' : 'text.primary' }}>
                          <Typography variant="body2">{m.content}</Typography>
                        </Paper>
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography color="text.secondary">Start a call to begin simulation</Typography>
                  </Box>
                )}
              </CardContent>
              {currentCall && (
                <Box sx={{ p: 2, borderTop: '1px solid #e2e8f0' }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField 
                      fullWidth 
                      value={messageInput} 
                      onChange={(e) => setMessageInput(e.target.value)} 
                      placeholder="Type message..." 
                      onKeyPress={handleKeyPress} 
                    />
                    <IconButton color="primary" onClick={sendMessage} disabled={!messageInput.trim()}><SendIcon /></IconButton>
                  </Box>
                </Box>
              )}
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card sx={{ bgcolor: '#0f172a', mb: 3 }}>
              <CardHeader title={<Typography color="white">Agent Reasoning</Typography>} avatar={<PsychologyIcon sx={{ color: '#60a5fa' }} />} />
              <CardContent sx={{ p: 0 }}><AgentThoughts thoughts={thoughts} reasoningData={reasoningData} /></CardContent>
            </Card>
            
            {latencyMetrics && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="overline">Nova Latency</Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Typography variant="body2">Reasoning:</Typography>
                    <Typography variant="body2" fontWeight="bold">{latencyMetrics.reasoning_ms}ms</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Speech:</Typography>
                    <Typography variant="body2" fontWeight="bold">{latencyMetrics.speech_ms}ms</Typography>
                  </Box>
                </CardContent>
              </Card>
            )}

            <AutomationProgress workflow={automationWorkflow} />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={2}>
          {quickTestScenarios.map((s, i) => (
            <Grid item xs={12} sm={4} key={i}>
              <Button fullWidth variant="outlined" sx={{ height: 100 }} onClick={() => handleQuickScenario(s)}>
                {s.emoji} {s.title}
              </Button>
            </Grid>
          ))}
        </Grid>
      </TabPanel>
    </Container>
  );
}
