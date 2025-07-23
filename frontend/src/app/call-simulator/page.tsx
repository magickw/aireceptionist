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
import { ConversationMessage, CallSession, ConversationContext } from '@/types/ai';
import AIConversationEngine from '@/services/aiConversationEngine';
import axios from 'axios';

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
  const [businessContext, setBusinessContext] = useState<any>(null);
  const [aiEngine, setAiEngine] = useState<AIConversationEngine | null>(null);
  const [completedActions, setCompletedActions] = useState<any[]>([]);
  const [callSummaryOpen, setCallSummaryOpen] = useState(false);
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
    const fetchBusinessContext = async () => {
      try {
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const business = businessResponse.data[0];
          
          // Create business-specific context based on type
          const getServicesForBusinessType = (businessType: string) => {
            switch (businessType) {
              case 'restaurant':
                return [
                  { id: '1', name: 'Table Reservation', description: 'Reserve a table for dining', duration: 120, price: 0, category: 'Dining' },
                  { id: '2', name: 'Private Event', description: 'Book private dining space', duration: 240, price: 200, category: 'Events' },
                  { id: '3', name: 'Catering Order', description: 'Order catering for events', duration: 60, price: 100, category: 'Catering' },
                ];
              case 'salon':
                return [
                  { id: '1', name: 'Haircut', description: 'Professional haircut and styling', duration: 45, price: 80, category: 'Hair' },
                  { id: '2', name: 'Hair Coloring', description: 'Professional hair coloring service', duration: 120, price: 150, category: 'Hair' },
                  { id: '3', name: 'Styling', description: 'Hair styling for special events', duration: 60, price: 100, category: 'Hair' },
                ];
              case 'medical':
                return [
                  { id: '1', name: 'General Consultation', description: 'General medical consultation', duration: 30, price: 150, category: 'Consultation' },
                  { id: '2', name: 'Specialist Consultation', description: 'Specialist medical consultation', duration: 45, price: 250, category: 'Consultation' },
                  { id: '3', name: 'Follow-up Visit', description: 'Follow-up medical visit', duration: 20, price: 100, category: 'Follow-up' },
                ];
              case 'spa':
                return [
                  { id: '1', name: 'Massage', description: 'Relaxing full body massage', duration: 60, price: 120, category: 'Wellness' },
                  { id: '2', name: 'Facial', description: 'Rejuvenating facial treatment', duration: 90, price: 150, category: 'Skincare' },
                  { id: '3', name: 'Body Treatment', description: 'Full body wellness treatment', duration: 120, price: 200, category: 'Wellness' },
                ];
              default:
                return [
                  { id: '1', name: 'Consultation', description: 'Initial consultation', duration: 30, price: 50, category: 'General' },
                  { id: '2', name: 'Service Appointment', description: 'General service appointment', duration: 60, price: 100, category: 'General' },
                ];
            }
          };

          const getMenuForRestaurant = (businessType: string) => {
            if (businessType === 'restaurant') {
              return [
                { id: '1', name: 'Caesar Salad', description: 'Fresh romaine lettuce with parmesan and croutons', price: 14.99, category: 'Salads', available: true },
                { id: '2', name: 'Grilled Salmon', description: 'Fresh Atlantic salmon with herbs', price: 28.99, category: 'Main Course', available: true },
                { id: '3', name: 'Pasta Carbonara', description: 'Classic Italian pasta with cream sauce and pancetta', price: 18.99, category: 'Pasta', available: true },
                { id: '4', name: 'Ribeye Steak', description: 'Premium cut ribeye steak cooked to perfection', price: 35.99, category: 'Main Course', available: true },
                { id: '5', name: 'Margherita Pizza', description: 'Classic pizza with fresh mozzarella and basil', price: 16.99, category: 'Pizza', available: true },
                { id: '6', name: 'Chocolate Lava Cake', description: 'Decadent chocolate cake with molten center', price: 8.99, category: 'Desserts', available: true },
              ];
            }
            return [];
          };

          // Determine business type from business data or default to restaurant for testing
          const businessType = business.type || 'restaurant';
          
          const context = {
            ...business,
            type: businessType,
            services: getServicesForBusinessType(businessType),
            menu: getMenuForRestaurant(businessType),
          };
          
          console.log('🏢 Business context created:', context);
          
          setBusinessContext(context);
          setAiEngine(new AIConversationEngine(context));
        }
      } catch (error) {
        console.error('Error fetching business context:', error);
        // Fallback to restaurant context for testing
        const fallbackContext = {
          type: 'restaurant',
          name: 'AI Receptionist Test Restaurant',
          services: [
            { id: '1', name: 'Table Reservation', description: 'Reserve a table for dining', duration: 120, price: 0, category: 'Dining' },
            { id: '2', name: 'Private Event', description: 'Book private dining space', duration: 240, price: 200, category: 'Events' },
          ],
          menu: [
            { id: '1', name: 'Caesar Salad', description: 'Fresh romaine lettuce with parmesan', price: 14.99, category: 'Salads', available: true },
            { id: '2', name: 'Grilled Salmon', description: 'Fresh Atlantic salmon', price: 28.99, category: 'Main Course', available: true },
          ],
          operatingHours: {
            0: { open: 11, close: 22, closed: false },
            1: { open: 11, close: 22, closed: false },
            2: { open: 11, close: 22, closed: false },
            3: { open: 11, close: 22, closed: false },
            4: { open: 11, close: 22, closed: false },
            5: { open: 11, close: 23, closed: false },
            6: { open: 11, close: 23, closed: false },
          }
        };
        console.log('🏢 Using fallback restaurant context:', fallbackContext);
        setBusinessContext(fallbackContext);
        setAiEngine(new AIConversationEngine(fallbackContext));
      }
    };

    fetchBusinessContext();
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
          businessType: businessContext?.type || 'business',
          services: businessContext?.services || [],
          operatingHours: businessContext?.operatingHours || {},
          menu: businessContext?.menu || [],
        },
      },
    };

    setCurrentCall(newCall);
    setCompletedActions([]);

    // AI greeting
    setTimeout(() => {
      addAIMessage("Hello! Thank you for calling. I'm your AI assistant. How can I help you today?");
    }, 1000);
  };

  const endCall = () => {
    if (!currentCall || !aiEngine) return;

    const updatedCall = {
      ...currentCall,
      status: 'ended' as const,
      endTime: new Date(),
      summary: aiEngine.generateCallSummary(currentCall.messages, currentCall.context),
    };

    setCurrentCall(updatedCall);
    setCallSummaryOpen(true);
  };

  const addMessage = (content: string, sender: 'customer' | 'ai', type: 'text' | 'action' | 'system' = 'text') => {
    if (!currentCall) {
      console.error('❌ Cannot add message - no current call');
      return;
    }

    try {
      const message: ConversationMessage = {
        id: `msg-${Date.now()}-${Math.random()}`,
        timestamp: new Date(),
        sender,
        content,
        type,
      };

      console.log('➕ Adding message:', message);

      setCurrentCall(prevCall => {
        if (!prevCall) return prevCall;
        
        return {
          ...prevCall,
          messages: [...prevCall.messages, message],
        };
      });
    } catch (error) {
      console.error('❌ Error adding message:', error);
    }
  };

  const addAIMessage = (content: string, type: 'text' | 'action' | 'system' = 'text') => {
    addMessage(content, 'ai', type);
  };

  const sendMessage = async () => {
    if (!messageInput.trim() || !currentCall || !aiEngine) {
      console.log('❌ Cannot send message - missing requirements:', {
        messageInput: messageInput.trim(),
        currentCall: !!currentCall,
        aiEngine: !!aiEngine
      });
      return;
    }

    const userMessage = messageInput.trim();
    console.log('📤 Sending message:', userMessage);
    
    // Store the message first, then clear the input
    const messageCopy = userMessage;
    setMessageInput('');
    setIsProcessing(true);

    try {
      // Add user message to conversation
      console.log('➕ Adding user message to conversation');
      addMessage(messageCopy, 'customer');

      // Process with AI
      console.log('🤖 Starting AI processing...');
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate processing time

      const aiResponse = await aiEngine.processMessage(messageCopy, currentCall.context);
      console.log('🤖 AI response received:', aiResponse);
      
      // Add AI response
      if (aiResponse && aiResponse.message) {
        console.log('➕ Adding AI response to conversation');
        addAIMessage(aiResponse.message);
      } else {
        console.error('❌ No message in AI response:', aiResponse);
        addAIMessage("I apologize, I didn't quite understand that. Could you please rephrase your request?");
      }

      // Execute actions
      if (aiResponse.actions && Array.isArray(aiResponse.actions) && aiResponse.actions.length > 0) {
        console.log('🎬 Executing actions:', aiResponse.actions);
        for (const action of aiResponse.actions) {
          await executeAction(action);
        }
      }

      // Update call context with any changes
      setCurrentCall(prevCall => {
        if (!prevCall) return prevCall;
        
        return {
          ...prevCall,
          context: {
            ...prevCall.context,
            intent: aiResponse.intent || prevCall.context.intent,
            customerInfo: {
              ...prevCall.context.customerInfo,
              ...(aiResponse.entities?.name && { name: aiResponse.entities.name }),
              ...(aiResponse.entities?.phone && { phone: aiResponse.entities.phone }),
              ...(aiResponse.entities?.email && { email: aiResponse.entities.email }),
            }
          }
        };
      });

    } catch (error) {
      console.error('❌ Error processing message:', error);
      addAIMessage("I apologize, I'm having trouble processing your request. Let me connect you with a human agent.");
    } finally {
      console.log('✅ Message processing complete');
      setIsProcessing(false);
    }
  };

  const executeAction = async (action: any) => {
    switch (action.type) {
      case 'create_booking':
        await createBooking(action.data);
        break;
      case 'create_order':
        await createOrder(action.data);
        break;
      case 'transfer_call':
        addAIMessage("I'm transferring you to a specialist who can better assist you.", 'system');
        break;
    }
  };

  const createBooking = async (bookingData: any) => {
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
      addAIMessage(`✅ Perfect! I've successfully booked your ${bookingData.service} appointment for ${bookingData.date} at ${bookingData.time}. You'll receive a confirmation shortly.`, 'action');
      
    } catch (error) {
      addAIMessage("I'm sorry, there was an issue creating your booking. Let me connect you with someone who can help.");
    }
  };

  const createOrder = async (orderData: any) => {
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
      addAIMessage(`✅ Great! Your order has been placed. Total: $${orderData.total?.toFixed(2) || '0.00'}. We'll have it ready for you soon!`, 'action');
      
    } catch (error) {
      addAIMessage("I'm sorry, there was an issue placing your order. Let me connect you with someone who can help.");
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      event.stopPropagation();
      sendMessage();
    }
  };

  const handleSendClick = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    sendMessage();
  };

  const useTestScenario = (scenario: any) => {
    if (!currentCall) {
      startCall();
      setTimeout(() => {
        setMessageInput(scenario.starter || scenario.script);
      }, 1500);
    } else {
      setMessageInput(scenario.starter || scenario.script);
    }
  };

  const useQuickScenario = (scenario: any) => {
    console.log('🎯 Using quick scenario:', scenario.title);
    
    try {
      if (!currentCall) {
        console.log('🎯 Starting new call for scenario');
        startCall();
        setTimeout(() => {
          console.log('🎯 Setting message input after call start:', scenario.script);
          setMessageInput(scenario.script);
        }, 1500);
      } else {
        console.log('🎯 Setting message input for existing call:', scenario.script);
        setMessageInput(scenario.script);
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
                <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
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
                        onClick={() => useQuickScenario(scenario)}
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

          {/* Call Info & Actions */}
          <Grid item xs={12} lg={4}>
            <Grid container spacing={2}>
              {/* Call Context */}
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Call Context" />
                  <CardContent>
                    {currentCall ? (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>Customer Info:</Typography>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            Name: {currentCall.context.customerInfo.name || 'Not provided'}
                          </Typography>
                          <Typography variant="body2">
                            Phone: {currentCall.context.customerInfo.phone || 'Not provided'}
                          </Typography>
                          <Typography variant="body2">
                            Email: {currentCall.context.customerInfo.email || 'Not provided'}
                          </Typography>
                        </Box>

                        <Typography variant="subtitle2" gutterBottom>Intent:</Typography>
                        <Chip label={currentCall.context.intent} color="primary" size="small" sx={{ mb: 2 }} />

                        {currentCall.context.bookingInfo && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" gutterBottom>Booking Info:</Typography>
                            <Typography variant="body2">
                              Service: {currentCall.context.bookingInfo.service || 'Not specified'}
                            </Typography>
                            <Typography variant="body2">
                              Date: {currentCall.context.bookingInfo.date || 'Not specified'}
                            </Typography>
                            <Typography variant="body2">
                              Time: {currentCall.context.bookingInfo.time || 'Not specified'}
                            </Typography>
                            <Chip
                              label={currentCall.context.bookingInfo.completed ? 'Complete' : 'Incomplete'}
                              color={currentCall.context.bookingInfo.completed ? 'success' : 'warning'}
                              size="small"
                              sx={{ mt: 1 }}
                            />
                          </Box>
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Start a call to see context information
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Completed Actions */}
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Actions Completed" />
                  <CardContent>
                    {completedActions.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">
                        No actions completed yet
                      </Typography>
                    ) : (
                      <List sx={{ p: 0 }}>
                        {completedActions.map((action, index) => (
                          <ListItem key={index} sx={{ p: 1 }}>
                            <Avatar sx={{ mr: 2, bgcolor: 'success.main' }}>
                              {action.type === 'booking' ? <EventIcon /> : <ShoppingCartIcon />}
                            </Avatar>
                            <ListItemText
                              primary={
                                action.type === 'booking' 
                                  ? `Appointment Booked: ${action.data.service}`
                                  : `Order Placed: $${action.data.total?.toFixed(2)}`
                              }
                              secondary={`Customer: ${action.data.customerName}`}
                            />
                            <CheckCircleIcon color="success" />
                          </ListItem>
                        ))}
                      </List>
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
                            onClick={() => useTestScenario(scenario)}
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
          Call Summary
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