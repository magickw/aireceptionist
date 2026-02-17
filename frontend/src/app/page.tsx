"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Container, Typography, Button, Grid, Card, CardContent, CardActions, Chip, Stack, Divider, useTheme, alpha } from '@mui/material';
import { 
  Phone, 
  SmartToy, 
  CalendarMonth, 
  Restaurant, 
  MedicalServices, 
  LocalAtm,
  TrendingUp,
  Speed,
  Security,
  CloudUpload,
  Psychology,
  Settings,
  ArrowForward,
  CheckCircle,
  Star,
  StarBorder
} from '@mui/icons-material';
import { useAuth } from '@/context/AuthContext';

const features = [
  {
    icon: <Phone fontSize="large" />,
    title: "Voice Receptionist",
    description: "24/7 AI-powered phone answering with natural speech-to-speech conversations",
    path: "/call-management",
    color: "primary",
    tags: ["Real-time", "Natural Language", "Multi-turn"]
  },
  {
    icon: <SmartToy fontSize="large" />,
    title: "AI Chatbot",
    description: "Intelligent web chat assistant for customer inquiries and support",
    path: "/chatbot",
    color: "secondary",
    tags: ["Web Widget", "Context-aware", "Smart"]
  },
  {
    icon: <CalendarMonth fontSize="large" />,
    title: "Appointment Scheduling",
    description: "Automated booking with calendar integration and smart scheduling",
    path: "/appointments",
    color: "success",
    tags: ["Calendly", "Google Calendar", "Auto-confirm"]
  },
  {
    icon: <Restaurant fontSize="large" />,
    title: "Order Management",
    description: "Take and process orders for restaurants and retail businesses",
    path: "/orders",
    color: "warning",
    tags: ["Menu-based", "Multi-item", "Payment"]
  },
  {
    icon: <MedicalServices fontSize="large" />,
    title: "Healthcare Support",
    description: "Specialized templates for medical and dental clinics",
    path: "/business-setup",
    color: "error",
    tags: ["HIPAA-ready", "Emergency detection", "Safe"]
  },
  {
    icon: <LocalAtm fontSize="large" />,
    title: "Payment Processing",
    description: "Secure payment collection and order confirmation",
    path: "/orders",
    color: "info",
    tags: ["PCI Compliant", "Fast", "Secure"]
  }
];

const businessTypes = [
  { name: "Restaurant", icon: "🍽️", description: "Food orders, reservations, delivery" },
  { name: "Medical", icon: "🏥", description: "Appointments, patient inquiries, triage" },
  { name: "Dental", icon: "🦷", description: "Scheduling, insurance, procedures" },
  { name: "Salon", icon: "💇", description: "Bookings, services, availability" },
  { name: "Fitness", icon: "💪", description: "Membership, classes, scheduling" },
  { name: "Retail", icon: "🛒", description: "Orders, inventory, support" },
  { name: "Auto Repair", icon: "🔧", description: "Appointments, parts, diagnostics" },
  { name: "Real Estate", icon: "🏠", description: "Showings, inquiries, follow-ups" },
  { name: "Law Firm", icon: "⚖️", description: "Consultations, scheduling, intake" },
  { name: "Education", icon: "📚", description: "Enrollments, courses, support" },
  { name: "Hotel", icon: "🏨", description: "Reservations, services, check-in" },
  { name: "HVAC", icon: "❄️", description: "Emergency repairs, maintenance" },
  { name: "Accounting", icon: "📊", description: "Tax, consultations, documents" },
  { name: "General", icon: "🏢", description: "Customizable for any business" }
];

const stats = [
  { value: "24/7", label: "Availability", icon: <Phone /> },
  { value: "99%", label: "AI Accuracy", icon: <Psychology /> },
  { value: "<2s", label: "Response Time", icon: <Speed /> },
  { value: "14+", label: "Business Types", icon: <TrendingUp /> }
];

export default function LandingPage() {
  const router = useRouter();
  const auth = useAuth();
  const isAuthenticated = auth?.isAuthenticated || false;

  const handleNavigate = (path: string) => {
    router.push(path);
  };

  // Redirect to dashboard if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  if (isAuthenticated) {
    return null;
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
          py: { xs: 8, md: 12 },
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Container maxWidth="xl">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant="h2"
                component="h1"
                gutterBottom
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: '2.5rem', md: '3.5rem' },
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 3
                }}
              >
                AI Receptionist
                <br />
                for Your Business
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                gutterBottom
                sx={{ fontSize: { xs: '1.1rem', md: '1.25rem' }, mb: 4 }}
              >
                Transform your customer interactions with intelligent voice and chat automation.
                Handle calls, appointments, orders, and support 24/7 with natural AI conversations.
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => handleNavigate('/login')}
                  startIcon={<Phone />}
                  sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
                >
                  Get Started Free
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => handleNavigate('/call-simulator')}
                  startIcon={<SmartToy />}
                  sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
                >
                  Try Demo
                </Button>
              </Stack>
              <Box sx={{ mt: 4, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Chip icon={<CheckCircle />} label="No credit card required" size="small" />
                <Chip icon={<CheckCircle />} label="14+ business types" size="small" />
                <Chip icon={<CheckCircle />} label="Setup in minutes" size="small" />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card
                sx={{
                  p: 4,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  color: 'white',
                  boxShadow: 8,
                  borderRadius: 4
                }}
              >
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Powered by Nova AI
                </Typography>
                <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
                  Advanced reasoning engine with intent detection, entity extraction, and autonomous action execution.
                </Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Star sx={{ color: '#FFD700' }} />
                    <Typography>Three-layer governance for safety</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Star sx={{ color: '#FFD700' }} />
                    <Typography>Context-aware conversations</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Star sx={{ color: '#FFD700' }} />
                    <Typography>Multi-modal support (voice, text, images)</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Star sx={{ color: '#FFD700' }} />
                    <Typography>Enterprise-grade security</Typography>
                  </Box>
                </Stack>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="xl" sx={{ py: 8 }}>
        <Grid container spacing={4} justifyContent="center">
          {stats.map((stat, index) => (
            <Grid item xs={6} md={3} key={index}>
              <Box sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    display: 'inline-flex',
                    p: 2,
                    borderRadius: '50%',
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    color: theme.palette.primary.main,
                    mb: 2
                  }}
                >
                  {stat.icon}
                </Box>
                <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stat.label}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Features Section */}
      <Container maxWidth="xl" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          gutterBottom
          sx={{ textAlign: 'center', fontWeight: 'bold', mb: 2 }}
        >
          Powerful Features for Every Business
        </Typography>
        <Typography
          variant="h6"
          color="text.secondary"
          sx={{ textAlign: 'center', mb: 6, maxWidth: 700, mx: 'auto' }}
        >
          Our AI receptionist handles all your customer interactions with natural conversations and intelligent automation
        </Typography>
        <Grid container spacing={3}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6
                  }
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      p: 2,
                      borderRadius: 2,
                      bgcolor: alpha(theme.palette[feature.color as keyof typeof theme.palette].main, 0.1),
                      color: theme.palette[feature.color as keyof typeof theme.palette].main,
                      mb: 3
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {feature.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {feature.tags.map((tag, tagIndex) => (
                      <Chip
                        key={tagIndex}
                        label={tag}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    ))}
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    onClick={() => handleNavigate(feature.path)}
                    endIcon={<ArrowForward />}
                    sx={{ ml: 1 }}
                  >
                    Learn More
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      <Divider sx={{ my: 4 }} />

      {/* Business Types Section */}
      <Container maxWidth="xl" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          gutterBottom
          sx={{ textAlign: 'center', fontWeight: 'bold', mb: 2 }}
        >
          14+ Business Types Supported
        </Typography>
        <Typography
          variant="h6"
          color="text.secondary"
          sx={{ textAlign: 'center', mb: 6 }}
        >
          Specialized AI templates tailored for your industry
        </Typography>
        <Grid container spacing={2}>
          {businessTypes.map((type, index) => (
            <Grid item xs={6} sm={4} md={3} key={index}>
              <Card
                sx={{
                  p: 2,
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4
                  }
                }}
                onClick={() => handleNavigate('/business-setup')}
              >
                <Typography variant="h3" sx={{ mb: 1 }}>
                  {type.icon}
                </Typography>
                <Typography variant="body2" gutterBottom sx={{ fontWeight: 'bold' }}>
                  {type.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {type.description}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Admin Features Section */}
      <Container maxWidth="xl" sx={{ py: 8 }}>
        <Box
          sx={{
            background: `linear-gradient(135deg, ${alpha(theme.palette.secondary.main, 0.05)} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`,
            borderRadius: 4,
            p: 6
          }}
        >
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
                Advanced Admin Tools
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                Manage your AI receptionist with powerful administrative features
              </Typography>
              <Stack spacing={3}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Settings color="primary" />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      Template Management
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Customize AI behavior with database-driven templates, version control, and rollback support
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Psychology color="secondary" />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      AI Training
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Train your AI with custom scenarios and improve responses over time
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <CloudUpload color="success" />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      Knowledge Base
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Upload documents for AI reference using RAG (Retrieval-Augmented Generation)
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Security color="warning" />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      Enterprise Security
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Multi-tier governance, approval workflows, and comprehensive audit trails
                    </Typography>
                  </Box>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={12} md={6}>
              <Stack spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={() => handleNavigate('/admin/templates')}
                  startIcon={<Settings />}
                  sx={{ py: 2 }}
                >
                  Manage Templates
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  onClick={() => handleNavigate('/admin/business-type-suggestion')}
                  startIcon={<Psychology />}
                  sx={{ py: 2 }}
                >
                  AI Business Type Detection
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  onClick={() => handleNavigate('/knowledge-base')}
                  startIcon={<CloudUpload />}
                  sx={{ py: 2 }}
                >
                  Knowledge Base
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  onClick={() => handleNavigate('/ai-training')}
                  startIcon={<SmartToy />}
                  sx={{ py: 2 }}
                >
                  AI Training
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </Box>
      </Container>

      {/* CTA Section */}
      <Container maxWidth="md" sx={{ py: 12, textAlign: 'center' }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
          Ready to Transform Your Business?
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
          Join hundreds of businesses using AI Receptionist to automate customer interactions
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
          <Button
            variant="contained"
            size="large"
            onClick={() => handleNavigate('/login')}
            sx={{ px: 6, py: 2, fontSize: '1.1rem' }}
          >
            Start Free Trial
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={() => handleNavigate('/call-simulator')}
            sx={{ px: 6, py: 2, fontSize: '1.1rem' }}
          >
            Live Demo
          </Button>
        </Stack>
      </Container>

      {/* Footer */}
      <Box
        sx={{
          bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100',
          py: 6,
          mt: 4
        }}
      >
        <Container maxWidth="xl">
          <Grid container spacing={4}>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                AI Receptionist
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Transform your customer interactions with intelligent AI automation.
              </Typography>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                Features
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/call-management')}>
                  Voice Receptionist
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/chatbot')}>
                  AI Chatbot
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/appointments')}>
                  Appointments
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/orders')}>
                  Orders
                </Typography>
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                Admin
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/admin/templates')}>
                  Templates
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/ai-training')}>
                  AI Training
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/knowledge-base')}>
                  Knowledge Base
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/analytics')}>
                  Analytics
                </Typography>
              </Stack>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                Quick Links
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/business-setup')}>
                  Business Setup
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/call-simulator')}>
                  Call Simulator
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/integrations')}>
                  Integrations
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }} onClick={() => handleNavigate('/settings')}>
                  Settings
                </Typography>
              </Stack>
            </Grid>
          </Grid>
          <Divider sx={{ my: 4 }} />
          <Typography variant="body2" color="text.secondary" align="center">
            © 2026 AI Receptionist. All rights reserved. Powered by Nova AI Engine.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}