"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Container, Typography, Button, Grid, Card, CardContent, CardActions, Chip, Stack, Divider, useTheme, alpha, Fade, Slide } from '@mui/material';
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
  StarBorder,
  Headphones,
  SupportAgent,
  AutoFixHigh
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
  { name: "Barbershop", icon: "✂️", description: "Haircuts, beard trims, walk-ins" },
  { name: "Nail Salon", icon: "💅", description: "Manicures, pedicures, nail art" },
  { name: "Fitness", icon: "💪", description: "Membership, classes, scheduling" },
  { name: "Retail", icon: "🛒", description: "Orders, inventory, support" },
  { name: "Auto Repair", icon: "🔧", description: "Appointments, parts, diagnostics" },
  { name: "Real Estate", icon: "🏠", description: "Showings, inquiries, follow-ups" },
  { name: "Law Firm", icon: "⚖️", description: "Consultations, scheduling, intake" },
  { name: "Education", icon: "📚", description: "Enrollments, courses, support" },
  { name: "Hotel", icon: "🏨", description: "Reservations, services, check-in" },
  { name: "HVAC", icon: "❄️", description: "Emergency repairs, maintenance" },
  { name: "Plumbing", icon: "🔩", description: "Leak repair, drain cleaning, water heaters" },
  { name: "Electrical", icon: "⚡", description: "Wiring, panel upgrades, EV chargers" },
  { name: "Pest Control", icon: "🐛", description: "Inspections, treatments, prevention" },
  { name: "Chiropractic", icon: "🧘", description: "Back pain, adjustments, wellness care" },
  { name: "Physical Therapy", icon: "💪", description: "Rehabilitation, injury recovery, mobility" },
  { name: "Optometry", icon: "👁️", description: "Eye exams, glasses, contact lenses" },
  { name: "Urgent Care", icon: "🚑", description: "Walk-in care, minor emergencies, X-rays" },
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
  const theme = useTheme();

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
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          py: { xs: 6, sm: 8, md: 12 },
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'radial-gradient(circle at 20% 50%, rgba(37, 99, 235, 0.08) 0%, transparent 50%)',
            pointerEvents: 'none',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'radial-gradient(circle at 80% 50%, rgba(100, 116, 139, 0.08) 0%, transparent 50%)',
            pointerEvents: 'none',
          },
        }}
      >
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={{ xs: 4, md: 6 }} alignItems="center">
            <Grid item xs={12} md={6}>
              <Fade in timeout={800}>
                <Box>
                  <Chip
                    label="🚀 AI-Powered Receptionist"
                    size="small"
                    sx={{
                      mb: 3,
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      fontWeight: 600,
                      borderRadius: 20,
                    }}
                  />
                  <Typography
                    variant="h2"
                    component="h1"
                    gutterBottom
                    sx={{
                      fontWeight: 800,
                      fontSize: { xs: '2.25rem', sm: '2.75rem', md: '3.5rem' },
                      lineHeight: 1.1,
                      background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 50%, ${theme.palette.secondary.main} 100%)`,
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      mb: 2,
                    }}
                  >
                    Receptium
                    <br />
                    for Your Business
                  </Typography>
                  <Typography
                    variant="h6"
                    color="text.secondary"
                    gutterBottom
                    sx={{ fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' }, mb: 4, maxWidth: 600 }}
                  >
                    Transform your customer interactions with intelligent voice and chat automation.
                    Handle calls, appointments, orders, and support 24/7 with natural AI conversations.
                  </Typography>
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 4 }}>
                    <Button
                      variant="contained"
                      size="large"
                      onClick={() => handleNavigate('/login')}
                      startIcon={<Phone />}
                      sx={{
                        px: 4,
                        py: 1.75,
                        fontSize: '1rem',
                        fontWeight: 600,
                        borderRadius: 14,
                        boxShadow: '0 4px 14px 0 rgba(37, 99, 235, 0.39)',
                        '&:hover': {
                          boxShadow: '0 6px 20px 0 rgba(37, 99, 235, 0.23)',
                          transform: 'translateY(-2px)',
                        },
                      }}
                    >
                      Get Started Free
                    </Button>
                    <Button
                      variant="outlined"
                      size="large"
                      onClick={() => handleNavigate('/call-simulator')}
                      startIcon={<SmartToy />}
                      sx={{
                        px: 4,
                        py: 1.75,
                        fontSize: '1rem',
                        fontWeight: 600,
                        borderRadius: 14,
                        borderWidth: 2,
                        '&:hover': {
                          borderWidth: 2,
                          transform: 'translateY(-2px)',
                        },
                      }}
                    >
                      Try Demo
                    </Button>
                  </Stack>
                  <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                      <CheckCircle sx={{ color: theme.palette.success.main, fontSize: 20 }} />
                      <Typography variant="body2" color="text.secondary" fontWeight={500}>
                        No credit card required
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                      <CheckCircle sx={{ color: theme.palette.success.main, fontSize: 20 }} />
                      <Typography variant="body2" color="text.secondary" fontWeight={500}>
                        14+ business types
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                      <CheckCircle sx={{ color: theme.palette.success.main, fontSize: 20 }} />
                      <Typography variant="body2" color="text.secondary" fontWeight={500}>
                        Setup in minutes
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Fade>
            </Grid>
            <Grid item xs={12} md={6}>
              <Slide direction="left" in timeout={1000}>
                <Card
                  sx={{
                    p: { xs: 3, md: 4 },
                    background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                    color: 'white',
                    boxShadow: '0 20px 40px -10px rgba(37, 99, 235, 0.4)',
                    borderRadius: { xs: 3, md: 4 },
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: 'rgba(255, 255, 255, 0.15)',
                        backdropFilter: 'blur(10px)',
                      }}
                    >
                      <AutoFixHigh />
                    </Box>
                    <Typography variant="h5" gutterBottom sx={{ fontWeight: 700, m: 0 }}>
                      Powered by Nova AI
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ mb: 4, opacity: 0.95, lineHeight: 1.7 }}>
                    Advanced reasoning engine with intent detection, entity extraction, and autonomous action execution.
                  </Typography>
                  <Stack spacing={2.5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Star sx={{ color: '#FFD700', fontSize: 24 }} />
                      <Typography sx={{ fontWeight: 500 }}>Three-layer governance for safety</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Star sx={{ color: '#FFD700', fontSize: 24 }} />
                      <Typography sx={{ fontWeight: 500 }}>Context-aware conversations</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Star sx={{ color: '#FFD700', fontSize: 24 }} />
                      <Typography sx={{ fontWeight: 500 }}>Multi-modal support (voice, text, images)</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Star sx={{ color: '#FFD700', fontSize: 24 }} />
                      <Typography sx={{ fontWeight: 500 }}>Enterprise-grade security</Typography>
                    </Box>
                  </Stack>
                </Card>
              </Slide>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="xl" sx={{ py: { xs: 6, md: 10 } }}>
        <Grid container spacing={3} justifyContent="center">
          {stats.map((stat, index) => (
            <Grid item xs={6} md={3} key={index}>
              <Box sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    display: 'inline-flex',
                    p: { xs: 1.5, sm: 2 },
                    borderRadius: '50%',
                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                    color: theme.palette.primary.main,
                    mb: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.15),
                      transform: 'scale(1.1)',
                    },
                  }}
                >
                  {stat.icon}
                </Box>
                <Typography
                  variant="h3"
                  gutterBottom
                  sx={{
                    fontWeight: 800,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontSize: { xs: '2rem', md: '2.5rem' },
                  }}
                >
                  {stat.value}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  {stat.label}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Features Section */}
      <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02), py: { xs: 8, md: 12 } }}>
        <Container maxWidth="xl">
          <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 8 } }}>
            <Typography
              variant="h3"
              component="h2"
              gutterBottom
              sx={{ fontWeight: 800, mb: 2, fontSize: { xs: '1.75rem', md: '2.25rem' } }}
            >
              Powerful Features for Every Business
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ maxWidth: 700, mx: 'auto', lineHeight: 1.6 }}
            >
              Our AI receptionist handles all your customer interactions with natural conversations and intelligent automation
            </Typography>
          </Box>
          <Grid container spacing={3}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    border: '1px solid rgba(226, 232, 240, 0.8)',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.15)',
                      borderColor: theme.palette[feature.color as keyof typeof theme.palette].main,
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, pt: 3 }}>
                    <Box
                      sx={{
                        display: 'inline-flex',
                        p: 2.5,
                        borderRadius: 3,
                        bgcolor: alpha(theme.palette[feature.color as keyof typeof theme.palette].main, 0.1),
                        color: theme.palette[feature.color as keyof typeof theme.palette].main,
                        mb: 3,
                        transition: 'all 0.3s ease',
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 700, fontSize: '1.125rem' }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3, lineHeight: 1.6 }}>
                      {feature.description}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {feature.tags.map((tag, tagIndex) => (
                        <Chip
                          key={tagIndex}
                          label={tag}
                          size="small"
                          variant="outlined"
                          sx={{
                            fontSize: '0.75rem',
                            fontWeight: 500,
                            borderRadius: 8,
                            borderColor: alpha(theme.palette[feature.color as keyof typeof theme.palette].main, 0.3),
                            color: theme.palette[feature.color as keyof typeof theme.palette].main,
                          }}
                        />
                      ))}
                    </Box>
                  </CardContent>
                  <CardActions sx={{ p: 3, pt: 0 }}>
                    <Button
                      onClick={() => handleNavigate(feature.path)}
                      endIcon={<ArrowForward />}
                      sx={{
                        ml: 0,
                        fontWeight: 600,
                        color: theme.palette[feature.color as keyof typeof theme.palette].main,
                        '&:hover': {
                          bgcolor: alpha(theme.palette[feature.color as keyof typeof theme.palette].main, 0.05),
                        }
                      }}
                    >
                      Learn More
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Business Types Section */}
      <Container maxWidth="xl" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          gutterBottom
          sx={{ textAlign: 'center', fontWeight: 'bold', mb: 2 }}
        >
          23+ Business Types Supported
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
          Join hundreds of businesses using Receptium to automate customer interactions
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
                Receptium
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
            © 2026 Receptium. All rights reserved. Powered by Amazon Nova AI Engine.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}