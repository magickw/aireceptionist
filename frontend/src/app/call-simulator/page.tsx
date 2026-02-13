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
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Tooltip from '@mui/material/Tooltip';
import PhoneIcon from '@mui/icons-material/Phone';
import PhoneDisabledIcon from '@mui/icons-material/PhoneDisabled';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EventIcon from '@mui/icons-material/Event';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AgentThoughts from '@/components/AgentThoughts';
import AutomationProgress from '@/components/AutomationProgress';
import { ConversationMessage, CallSession, ConversationContext } from '@/types/ai';

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
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export default function CallSimulator() {
  const [tabValue, setTabValue] = useState(0);
  const [currentCall, setCurrentCall] = useState<CallSession | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [reasoningData, setReasoningData] = useState<{
    intent: string;
    confidence: number;
    entities: Record<string, any>;
    selected_action: string;
    action_reasoning: string;
    sentiment: string;
    escalation_risk: number;
    reasoning_chain: any[];
  } | null>(null);
  const [automationWorkflow, setAutomationWorkflow] = useState<any>(null);
  const [callSummaryOpen, setCallSummaryOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickTestScenarios = [
    {
      emoji: '🍽️',
      title: 'Book a table',
      script: "Hi, I'd like to make a reservation for dinner tonight. Table for 2 at 7 PM please.",
      category: 'restaurant'
    },
    {
      emoji: '🛍️',
      title: 'Place an order',
      script: "I'd like to place an order for delivery. Can I get a Caesar salad and the grilled chicken?",
      category: 'restaurant'
    },
    {
      emoji: '❓',
      title: 'Ask about hours',
      script: "What are your business hours? Are you open on weekends?",
      category: 'general'
    },
    {
      emoji: '🥗',
      title: 'Ask about menu',
      script: "What do you have on the menu today? Do you have any vegetarian options?",
      category: 'restaurant'
    },
    {
      emoji: '💇',
      title: 'Book appointment',
      script: "Hi, I need to schedule a haircut appointment for this Friday afternoon. What times are available?",
      category: 'salon'
    },
    {
      emoji: '💊',
      title: 'Medical appointment',
      script: "I need to see the doctor as soon as possible. Do you have any appointments available this week?",
      category: 'medical'
    },
    {
      emoji: '🚗',
      title: 'Service appointment',
      script: "My car needs an oil change. Can I schedule a service appointment for next week?",
      category: 'automotive'
    },
    {
      emoji: '💰',
      title: 'Ask about pricing',
      script: "How much do your services cost? Do you have a price list I can see?",
      category: 'general'
    },
    {
      emoji: '📞',
      title: 'Transfer to human',
      script: "This is complicated. Can I speak to a real person please? I need to talk to someone directly.",
      category: 'general'
    },
    {
      emoji: '😤',
      title: 'Customer complaint',
      script: "I'm very unhappy with my last visit. The service was terrible and I want to speak to a manager.",
      category: 'general'
    },
    {
      emoji: '📅',
      title: 'Reschedule appointment',
      script: "I need to reschedule my appointment for tomorrow. Can we move it to next week instead?",
      category: 'general'
    },
    {
      emoji: '📍',
      title: 'Ask about location',
      script: "Where are you located? Do you have parking available? What's your address?",
      category: 'general'
    }
  ];

  const testScenarios = [
    {
      id: 'booking-basic',
      title: 'Basic Appointment Booking',
      description: 'Customer wants to book a simple appointment',
      starter: "Hi, I'd like to book an appointment for tomorrow.",
      category: 'Booking',
    },
    {
      id: 'booking-specific',
      title: 'Specific Service Booking',
      description: 'Customer requests a specific service and time',
      starter: "I need to schedule a haircut for this Friday at 2 PM.",
      category: 'Booking',
    },
    {
      id: 'restaurant-order',
      title: 'Restaurant Order',
      description: 'Customer wants to place a food order',
      starter: "I'd like to order some food for delivery.",
      category: 'Ordering',
    },
    {
      id: 'business-hours',
      title: 'Business Hours Inquiry',
      description: 'Customer asks about operating hours',
      starter: "What are your business hours?",
      category: 'Information',
    },
    {
      id: 'services-inquiry',
      title: 'Services Information',
      description: 'Customer wants to know about available services',
      starter: "What services do you offer?",
      category: 'Information',
    },
    {
      id: 'pricing-inquiry',
      title: 'Pricing Information',
      description: 'Customer asks about service pricing',
      starter: "How much does a consultation cost?",
      category: 'Information',
    },
    {
      id: 'complaint',
      title: 'Customer Complaint',
      description: 'Customer has an issue to resolve',
      starter: "I had a terrible experience last time and want to speak to a manager.",
      category: 'Support',
    },
    {
      id: 'complex-booking',
      title: 'Complex Booking Request',
      description: 'Customer with multiple requirements',
      starter: "My name is Sarah Johnson, I need to book a spa treatment for next Tuesday afternoon, preferably around 3 PM. My number is 555-123-4567.",
      category: 'Booking',
    },
  ];

  useEffect(() => {
    // Connect to Python Backend WebSocket
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/voice/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'thought') {
        setThoughts(prev => [...prev, {
          step: data.step,
          message: data.message,
          timestamp: new Date()
        }]);
      } else if (data.type === 'reasoning_chain') {
        // Update reasoning data for visualization
        setReasoningData(prev => ({
          ...prev,
          reasoning_chain: data.data || []
        }));
      } else if (data.type === 'reasoning_complete') {
        // Store complete reasoning data
        setReasoningData({
          intent: data.data.intent,
          confidence: data.data.confidence,
          entities: {},
          selected_action: data.data.selected_action,
          action_reasoning: '',
          sentiment: data.data.sentiment,
          escalation_risk: data.data.escalation_risk,
          reasoning_chain: reasoningData?.reasoning_chain || []
        });
      } else if (data.type === 'agent_response') {
        setIsProcessing(false);
        addAIMessage(data.text);
        
        if (data.reasoning) {
          // Update with full reasoning data from response
          setReasoningData(data.reasoning);
          
          // Check if action requires automation
          if (data.reasoning.selected_action === 'CREATE_APPOINTMENT') {
            // Trigger automation workflow
            triggerAutomationWorkflow(data.reasoning);
          }
        }
        
        if (data.reasoning) {
          // Update with full reasoning data from response
          setReasoningData(data.reasoning);
        }
        
        // Audio will be sent separately as 'audio' event
      } else if (data.type === 'audio') {
        // Play audio from Nova Sonic
        // PCM16 format needs to be converted to playable format
        if (data.audio) {
          playPcm16Audio(data.audio, data.sample_rate || 16000);
        }
      } else if (data.type === 'audio_config') {
        // Store audio configuration
        console.log('Audio config received:', data.config);
      } else if (data.type === 'latency_metrics') {
        // Display latency metrics
        console.log('Latency metrics:', data.metrics);
      } else if (data.type === 'transcript') {
        // Customer transcript from audio input
        console.log('Transcript:', data.text);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [currentCall?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const startCall = (customerPhone: string = '+1 (555) 123-4567') => {
    const newCall: CallSession = {
      id: `call-${Date.now()}`,
      customerPhone,
      status: 'active',
      startTime: new Date(),
      messages: [],
      context: {
        customerInfo: {},
        intent: 'unknown',
        businessContext: {
          businessType: 'medical',
          services: [],
          operatingHours: {},
          menu: [],
        },
      },
    };

    setCurrentCall(newCall);
    setThoughts([]);
    
    setTimeout(() => {
      addAIMessage("Hello! Thank you for calling Smile Care Dental. I'm your AI assistant. How can I help you today?");
    }, 500);
  };

  const endCall = () => {
    if (!currentCall) return;
    setCurrentCall({
      ...currentCall,
      status: 'ended' as const,
      endTime: new Date(),
    });
  };

  const addMessage = (content: string, sender: 'customer' | 'ai', type: 'text' | 'action' | 'system' = 'text') => {
    const message: ConversationMessage = {
      id: `msg-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      sender,
      content,
      type,
    };

    setCurrentCall(prevCall => {
      if (!prevCall) return prevCall;
      return {
        ...prevCall,
        messages: [...prevCall.messages, message],
      };
    });
  };

  const addAIMessage = (content: string, type: 'text' | 'action' | 'system' = 'text') => {
    addMessage(content, 'ai', type);
  };

  const sendMessage = async () => {
    if (!messageInput.trim() || !currentCall || !wsRef.current) return;

    const userMessage = messageInput.trim();
    setMessageInput('');
    setIsProcessing(true);
    setThoughts([]); // Clear previous thoughts

    addMessage(userMessage, 'customer');

    // Send to WebSocket
    wsRef.current.send(JSON.stringify({
      type: 'user_input',
      text: userMessage
    }));
  };

  interface AIAction {
    type: 'create_booking' | 'create_order' | 'transfer_call' | 'request_info' | 'provide_info';
    data?: Record<string, unknown>;
  }

  const executeAction = async (action: AIAction) => {
    switch (action.type) {
      case 'create_booking':
        if (action.data) {
          await createBooking(action.data);
        }
        break;
      case 'create_order':
        if (action.data) {
          await createOrder(action.data);
        }
        break;
      case 'transfer_call':
        addAIMessage("I'm transferring you to a specialist who can better assist you.", 'system');
        break;
      case 'request_info':
      case 'provide_info':
        // Handle other action types
        console.log(`Handling ${action.type} action:`, action.data);
        break;
      default:
        console.warn(`Unhandled action type: ${action.type}`);
        break;
    }
  };

  const createBooking = async (bookingData: {service?: string, date?: string, time?: string, [key: string]: unknown}) => {
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const booking = {
        id: Date.now(),
        ...bookingData,
        status: 'confirmed',
        createdAt: new Date(),
      };

      setCompletedActions(prev => [...prev, { type: 'booking', data: booking }]);
      addAIMessage(`✅ Perfect! I've successfully booked your ${bookingData.service || 'requested'} appointment for ${bookingData.date || 'the requested date'} at ${bookingData.time || 'the requested time'}. You'll receive a confirmation shortly.`, 'action');
      
    } catch (error) {
      addAIMessage("I'm sorry, there was an issue creating your booking. Let me connect you with someone who can help.");
    }
  };

  const createOrder = async (orderData: {total?: number, items?: Array<Record<string, unknown>>, [key: string]: unknown}) => {
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const order = {
        id: Date.now(),
        ...orderData,
        status: 'confirmed',
        createdAt: new Date(),
      };

      setCompletedActions(prev => [...prev, { type: 'order', data: order }]);
      addAIMessage(`✅ Great! Your order has been placed. Total: $${orderData.total !== undefined ? orderData.total.toFixed(2) : '0.00'}. We'll have it ready for you soon!`, 'action');
      
    } catch (error) {
      addAIMessage("I'm sorry, there was an issue placing your order. Let me connect you with someone who can help.");
    }
  };

  const playPcm16Audio = (base64Audio: string, sampleRate: number) => {
    try {
      // Decode base64 to binary
      const audioData = atob(base64Audio);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new DataView(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view.setUint8(i, audioData.charCodeAt(i));
      }
      
      // Convert PCM16 to Float32 for Web Audio API
      const samples = new Int16Array(arrayBuffer);
      const float32Buffer = new Float32Array(samples.length);
      
      for (let i = 0; i < samples.length; i++) {
        // Convert 16-bit PCM to float (-1.0 to 1.0)
        float32Buffer[i] = samples[i] / 32768.0;
      }
      
      // Create audio context and play
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate });
      const audioBuffer = audioContext.createBuffer(1, float32Buffer.length, sampleRate);
      audioBuffer.getChannelData(0).set(float32Buffer);
      
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start(0);
      
      // Cleanup after playing
      source.onended = () => {
        audioContext.close();
      };
    } catch (error) {
      console.error('Error playing PCM16 audio:', error);
    }
  };

  const handleSendClick = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    sendMessage();
  };

  // Function to handle test scenarios
  const handleTestScenario = (scenario: {starter?: string, script?: string}) => {
    if (!currentCall) {
      startCall();
      setTimeout(() => {
        setMessageInput(scenario.starter || scenario.script || '');
      }, 1500);
    } else {
      setMessageInput(scenario.starter || scenario.script || '');
    }
  };

  // Function to handle quick scenarios
  const handleQuickScenario = (scenario: {title?: string, script?: string}) => {
    console.log('🎯 Using quick scenario:', scenario.title || 'Unnamed scenario');
    
    try {
      if (!currentCall) {
        console.log('🎯 Starting new call for scenario');
        startCall();
        setTimeout(() => {
          console.log('🎯 Setting message input after call start:', scenario.script || '');
          setMessageInput(scenario.script || '');
        }, 1500);
      } else {
        console.log('🎯 Setting message input for existing call:', scenario.script || '');
        setMessageInput(scenario.script || '');
      }
    } catch (error) {
      console.error('❌ Error in useQuickScenario:', error);
    }
  };

  const formatDuration = (startTime: Date, endTime?: Date) => {
    const end = endTime || new Date();
    const duration = Math.floor((end.getTime() - startTime.getTime()) / 1000);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const triggerAutomationWorkflow = async (reasoning: any) => {
    try {
      // Create automation workflow based on reasoning
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/automation/create-calendly-workflow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: reasoning.entities?.customer_name || 'Customer',
          customer_phone: currentCall?.customer_phone || '+1 (555) 123-4567',
          customer_email: 'customer@example.com',
          service: reasoning.entities?.service || 'Consultation',
          date: reasoning.entities?.date || 'Tomorrow',
          time: reasoning.entities?.time || '10:00 AM',
          calendly_url: 'https://calendly.com/example'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setAutomationWorkflow(result.workflow);
        
        // Execute workflow via WebSocket
        const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/api/automation/ws/${result.workflow.workflow_id}`);
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'workflow_started') {
            addAIMessage(`🤖 Nova Act is now executing: ${data.name}`, 'action');
          } else if (data.type === 'step_completed') {
            addAIMessage(`✓ ${data.description}`, 'action');
            setAutomationWorkflow(prev => ({
              ...prev,
              current_step: data.step_id,
              progress_percent: data.progress_percent
            }));
          } else if (data.type === 'workflow_completed') {
            addAIMessage(`✅ Automation complete! Booked ${result.workflow.metadata?.service} for ${result.workflow.metadata?.customer_name}`, 'action');
            setAutomationWorkflow(prev => ({
              ...prev,
              status: 'completed',
              progress_percent: 100
            }));
          } else if (data.type === 'workflow_failed') {
            addAIMessage(`❌ Automation failed: ${data.error}`, 'action');
            setAutomationWorkflow(prev => ({
              ...prev,
              status: 'failed'
            }));
          }
        };
        
        // Send workflow execution command
        ws.onopen = () => {
          ws.send(JSON.stringify({
            type: 'execute',
            workflow: result.workflow
          }));
        };
      }
    } catch (error) {
      console.error('Error triggering automation:', error);
      addAIMessage('Failed to start automation workflow', 'action');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 }, px: { xs: 2, sm: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 4 } }}>
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom 
          sx={{ 
            fontWeight: 'bold', 
            color: 'primary.main',
            fontSize: { xs: '1.75rem', sm: '2.125rem' }
          }}
        >
          AI Call Simulator
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          Test your AI receptionist with realistic call scenarios
        </Typography>
      </Box>

      <Tabs 
        value={tabValue} 
        onChange={handleTabChange} 
        sx={{ 
          mb: 3,
          '& .MuiTab-root': {
            fontSize: { xs: '0.875rem', sm: '1rem' },
            minWidth: { xs: 'auto', sm: 'auto' },
            px: { xs: 1, sm: 2 }
          }
        }}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
      >
        <Tab label="Call Simulation" />
        <Tab label="Test Scenarios" />
        <Tab label="Performance Analytics" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          {/* Call Interface */}
          <Grid item xs={12} lg={8}>
            <Card sx={{ height: { xs: '500px', sm: '600px' }, display: 'flex', flexDirection: 'column' }}>
              <CardHeader
                avatar={
                  <Avatar sx={{ bgcolor: currentCall?.status === 'active' ? 'success.main' : 'grey.500' }}>
                    <PhoneIcon />
                  </Avatar>
                }
                title={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="h6">
                      {currentCall ? `Call with ${currentCall.customerPhone}` : 'No Active Call'}
                    </Typography>
                    {currentCall && (
                      <Chip
                        label={currentCall.status.toUpperCase()}
                        color={currentCall.status === 'active' ? 'success' : 'default'}
                        size="small"
                      />
                    )}
                    {currentCall && (
                      <Chip
                        icon={useContextAware ? <PsychologyIcon /> : <SmartToyIcon />}
                        label={useContextAware ? "Context-Aware AI" : "Standard AI"}
                        color={useContextAware ? "primary" : "default"}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Box>
                }
                subheader={
                  currentCall && (
                    <Typography variant="body2">
                      Duration: {formatDuration(currentCall.startTime, currentCall.endTime)}
                    </Typography>
                  )
                }
                action={
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {!currentCall ? (
                      <Button
                        variant="contained"
                        color="success"
                        startIcon={<PhoneIcon />}
                        onClick={() => startCall()}
                      >
                        Start Call
                      </Button>
                    ) : currentCall.status === 'active' ? (
                      <Button
                        variant="contained"
                        color="error"
                        startIcon={<PhoneDisabledIcon />}
                        onClick={endCall}
                      >
                        End Call
                      </Button>
                    ) : (
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<PhoneIcon />}
                        onClick={() => startCall()}
                      >
                        New Call
                      </Button>
                    )}
                  </Box>
                }
              />
              
              {/* Messages */}
              <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
                <Box sx={{ 
                  flexGrow: 1, 
                  overflow: 'auto', 
                  p: 2,
                  height: 0, // Force flex child to respect parent height
                  overflowY: 'auto' // Ensure vertical scrolling
                }}>
                  {!currentCall ? (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        Start a call to begin testing
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Click "Start Call" to simulate an incoming customer call
                      </Typography>
                    </Box>
                  ) : (
                    <List sx={{ p: 0 }}>
                      {currentCall.messages.map((message) => (
                        <ListItem
                          key={message.id}
                          sx={{
                            flexDirection: 'column',
                            alignItems: message.sender === 'customer' ? 'flex-end' : 'flex-start',
                            p: 1,
                          }}
                        >
                          <Paper
                            sx={{
                              p: 2,
                              maxWidth: '80%',
                              bgcolor: message.sender === 'customer' ? 'primary.main' : 
                                      message.type === 'action' ? 'success.light' :
                                      message.type === 'system' ? 'warning.light' : 'grey.100',
                              color: message.sender === 'customer' ? 'primary.contrastText' : 'text.primary',
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <Avatar sx={{ width: 24, height: 24 }}>
                                {message.sender === 'customer' ? <PersonIcon /> : <SmartToyIcon />}
                              </Avatar>
                              <Typography variant="caption">
                                {message.sender === 'customer' ? 'Customer' : 'AI Assistant'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {message.timestamp.toLocaleTimeString()}
                              </Typography>
                            </Box>
                            <Typography variant="body2">{message.content}</Typography>
                          </Paper>
                        </ListItem>
                      ))}
                      {isProcessing && (
                        <ListItem sx={{ flexDirection: 'column', alignItems: 'flex-start', p: 1 }}>
                          <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Avatar sx={{ width: 24, height: 24 }}>
                                <SmartToyIcon />
                              </Avatar>
                              <Typography variant="caption">AI Assistant is thinking...</Typography>
                            </Box>
                            <LinearProgress sx={{ mt: 1, width: 200 }} />
                          </Paper>
                        </ListItem>
                      )}
                      <div ref={messagesEndRef} />
                    </List>
                  )}
                </Box>

                {/* Message Input */}
                {currentCall?.status === 'active' && (
                  <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
                    <Box component="form" onSubmit={(e) => { e.preventDefault(); handleSendClick(e as any); }} sx={{ display: 'flex', gap: 1 }}>
                      <TextField
                        fullWidth
                        variant="outlined"
                        placeholder="Type your message as the customer..."
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        disabled={isProcessing}
                        multiline
                        maxRows={3}
                      />
                      <IconButton
                        type="submit"
                        color="primary"
                        onClick={handleSendClick}
                        disabled={!messageInput.trim() || isProcessing}
                        sx={{ alignSelf: 'flex-end' }}
                      >
                        <SendIcon />
                      </IconButton>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Test Scenarios */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardHeader 
                title="Quick Test Scenarios" 
                subheader="Click any scenario to instantly test your AI with realistic customer requests"
              />
              <CardContent>
                <Grid container spacing={2}>
                  {quickTestScenarios.map((scenario, index) => (
                    <Grid item xs={6} sm={4} md={3} key={index}>
                      <Button
                        variant="outlined"
                        fullWidth
                        onClick={() => handleQuickScenario(scenario)}
                        sx={{
                          height: 80,
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 1,
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          p: 1,
                          border: '2px solid',
                          borderColor: 'primary.light',
                          '&:hover': {
                            borderColor: 'primary.main',
                            bgcolor: 'primary.50',
                          }
                        }}
                      >
                        <Typography variant="h5" component="span">
                          {scenario.emoji}
                        </Typography>
                        <Typography variant="caption" textAlign="center" sx={{ lineHeight: 1.2 }}>
                          {scenario.title}
                        </Typography>
                      </Button>
                    </Grid>
                  ))}
                </Grid>
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    💡 <strong>Tip:</strong> These scenarios automatically start a call and input realistic customer messages. 
                    Perfect for quickly testing how your AI handles common situations!
                  </Typography>
                </Alert>
              </CardContent>
            </Card>
          </Grid>

          {/* Call Context & Agent Thinking */}
          <Grid item xs={12} lg={4}>
            <Grid container spacing={2}>
              {/* Agent Thinking Panel */}
              <Grid item xs={12}>
                <Card sx={{ bgcolor: '#0f172a' }}>
                  <CardHeader 
                    title={<Typography color="white">Agent Reasoning (Live)</Typography>}
                    avatar={<PsychologyIcon sx={{ color: '#60a5fa' }} />}
                  />
                  <CardContent sx={{ p: 0 }}>
                    <AgentThoughts thoughts={thoughts} reasoningData={reasoningData} />
                  </CardContent>
                </Card>
              </Grid>

              {/* Automation Progress Panel */}
              <Grid item xs={12}>
                <AutomationProgress workflow={automationWorkflow} compact={false} />
              </Grid>

              {/* Call Info & Metadata */}
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Call Metadata" />
                  <CardContent>
                    {currentCall ? (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>Session ID:</Typography>
                        <Typography variant="body2" sx={{ mb: 2, fontMono: true }}>{currentCall.id}</Typography>
                        
                        <Typography variant="subtitle2" gutterBottom>Customer Phone:</Typography>
                        <Typography variant="body2" sx={{ mb: 2 }}>{currentCall.customerPhone}</Typography>

                        <Typography variant="subtitle2" gutterBottom>Model Pipeline:</Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Chip label="Nova 2 Sonic" size="small" color="primary" />
                          <Chip label="Nova 2 Lite" size="small" color="secondary" />
                          <Chip label="Nova Act" size="small" variant="outlined" />
                        </Box>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Start a call to see session metadata
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Test Scenarios */}
        <Grid container spacing={3}>
          {['Booking', 'Ordering', 'Information', 'Support'].map((category) => (
            <Grid item xs={12} md={6} key={category}>
              <Card>
                <CardHeader title={`${category} Scenarios`} />
                <CardContent>
                  <List>
                    {testScenarios
                      .filter(scenario => scenario.category === category)
                      .map((scenario) => (
                        <ListItem key={scenario.id} divider>
                          <ListItemText
                            primary={scenario.title}
                            secondary={scenario.description}
                          />
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => handleTestScenario(scenario)}
                          >
                            Test
                          </Button>
                        </ListItem>
                      ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Performance Analytics */}
        <Card>
          <CardHeader title="AI Performance Analytics" />
          <CardContent>
            <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              Performance analytics will show after completing test calls.
              Metrics include response accuracy, conversation success rate, and customer satisfaction scores.
            </Typography>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Call Summary Dialog */}
      <Dialog
        open={callSummaryOpen}
        onClose={() => setCallSummaryOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            m: { xs: 2, sm: 3 },
            maxHeight: { xs: 'calc(100vh - 64px)', sm: 'calc(100vh - 128px)' }
          }
        }}
      >
        <DialogTitle sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Call Summary</Typography>
            <Chip 
              icon={useContextAware ? <PsychologyIcon /> : <SmartToyIcon />}
              label={useContextAware ? "Generated by Context-Aware AI" : "Generated by Standard AI"}
              color={useContextAware ? "primary" : "default"}
              size="small"
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          {currentCall?.summary && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Satisfaction Score</Typography>
                <Typography variant="h4" color="primary">
                  {currentCall.summary.satisfactionScore.toFixed(1)}/5.0
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>Resolution Status</Typography>
                <Chip
                  label={currentCall.summary.resolved ? 'Resolved' : 'Unresolved'}
                  color={currentCall.summary.resolved ? 'success' : 'warning'}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Actions Taken</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {currentCall.summary.actionsTaken.map((action, index) => (
                    <Chip key={index} label={action} variant="outlined" />
                  ))}
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Key Topics</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {currentCall.summary.keyTopics.map((topic, index) => (
                    <Chip key={index} label={topic} color="primary" variant="outlined" />
                  ))}
                </Box>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCallSummaryOpen(false)}>Close</Button>
          <Button variant="contained" onClick={() => startCall()}>
            Start New Call
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}