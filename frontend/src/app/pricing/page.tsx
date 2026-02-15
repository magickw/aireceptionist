'use client';
import * as React from 'react';
import { 
  Container, Typography, Box, Grid, Card, CardContent, Button, 
  List, ListItem, ListItemIcon, ListItemText, Divider, Chip,
  useTheme, Paper
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import BoltIcon from '@mui/icons-material/Bolt';
import BusinessIcon from '@mui/icons-material/Business';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';

const PRICING_PLANS = [
  {
    title: 'Starter',
    price: '49',
    description: 'Perfect for small local businesses starting with AI automation.',
    features: [
      'Nova 2 Lite Reasoning Engine',
      'Text-based AI Chatbot',
      'Basic Intent Extraction',
      'Up to 100 calls/month',
      'Knowledge Base (10 documents)',
      'Email Support'
    ],
    buttonText: 'Start Free Trial',
    buttonVariant: 'outlined',
    icon: <BoltIcon color="primary" />,
    popular: false
  },
  {
    title: 'Professional',
    price: '149',
    description: 'Advanced features for growing businesses needing voice and automation.',
    features: [
      'Everything in Starter',
      'Nova 2 Sonic Voice AI (Low Latency)',
      'Nova Act UI Automation (Calendly)',
      'Up to 1,000 calls/month',
      'CRM Integrations (Salesforce)',
      'Advanced Analytics Dashboard',
      'Priority Support'
    ],
    buttonText: 'Get Started',
    buttonVariant: 'contained',
    icon: <RocketLaunchIcon color="primary" />,
    popular: true
  },
  {
    title: 'Enterprise',
    price: 'Custom',
    description: 'Full-scale autonomous operations for high-volume enterprises.',
    features: [
      'Everything in Professional',
      'Nova Multimodal Embeddings',
      'Custom AI Training Scenarios',
      'Unlimited Knowledge Base',
      'Dedicated Instance',
      'SLA & Account Manager',
      'Custom UI Workflows'
    ],
    buttonText: 'Contact Sales',
    buttonVariant: 'outlined',
    icon: <BusinessIcon color="primary" />,
    popular: false
  }
];

export default function PlatformPricingPage() {
  const theme = useTheme();

  return (
    <Container maxWidth="lg" sx={{ mt: 8, mb: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 8 }}>
        <Typography variant="overline" color="primary" fontWeight="bold" gutterBottom sx={{ letterSpacing: 2 }}>
          PRICING PLANS
        </Typography>
        <Typography variant="h3" component="h1" gutterBottom fontWeight="800">
          Scale Your Business with Nova
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto', fontWeight: 400 }}>
          Flexible plans designed to grow with your business. Choose the power of Amazon Nova that fits your operational needs.
        </Typography>
      </Box>

      <Grid container spacing={4} alignItems="stretch">
        {PRICING_PLANS.map((plan) => (
          <Grid item xs={12} md={4} key={plan.title}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                position: 'relative',
                transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: theme.shadows[10],
                },
                ...(plan.popular && {
                  border: `2px solid ${theme.palette.primary.main}`,
                  boxShadow: theme.shadows[5],
                })
              }}
            >
              {plan.popular && (
                <Chip 
                  label="MOST POPULAR" 
                  color="primary" 
                  size="small" 
                  sx={{ 
                    position: 'absolute', 
                    top: 16, 
                    right: 16, 
                    fontWeight: 'bold',
                    fontSize: '0.65rem'
                  }} 
                />
              )}
              <CardContent sx={{ p: 4, flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {plan.icon}
                  <Typography variant="h5" component="h2" sx={{ ml: 1, fontWeight: 'bold' }}>
                    {plan.title}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 2 }}>
                  <Typography variant="h3" component="span" fontWeight="800">
                    {plan.price === 'Custom' ? plan.price : `$${plan.price}`}
                  </Typography>
                  {plan.price !== 'Custom' && (
                    <Typography variant="h6" color="text.secondary" sx={{ ml: 1 }}>
                      /mo
                    </Typography>
                  )}
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 4, height: 40 }}>
                  {plan.description}
                </Typography>
                
                <Divider sx={{ mb: 4 }} />
                
                <List sx={{ mb: 4 }}>
                  {plan.features.map((feature) => (
                    <ListItem key={feature} disableGutters sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <CheckCircleIcon color="primary" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={feature} 
                        primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }} 
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
              <Box sx={{ p: 4, pt: 0 }}>
                <Button 
                  fullWidth 
                  variant={plan.buttonVariant as any} 
                  size="large"
                  sx={{ fontWeight: 'bold', py: 1.5 }}
                >
                  {plan.buttonText}
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 10 }}>
        <Paper 
          elevation={0} 
          sx={{ 
            p: 6, 
            borderRadius: 4, 
            bgcolor: '#f8fafc', 
            border: '1px solid #e2e8f0',
            textAlign: 'center'
          }}
        >
          <AutoAwesomeIcon sx={{ fontSize: 40, color: 'primary.main', mb: 2 }} />
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Special Hackathon Preview
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 800, mx: 'auto', mb: 4 }}>
            All features including <strong>Nova 2 Sonic</strong> and <strong>Nova Act</strong> are currently available 
            for live demonstration as part of our Amazon Nova Hackathon submission. 
            Experience the future of autonomous business today.
          </Typography>
          <Button variant="contained" color="primary" size="large" href="/call-simulator">
            Try the Live Demo
          </Button>
        </Paper>
      </Box>

      <Box sx={{ mt: 8, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Questions about our enterprise features? <Button color="primary" sx={{ fontWeight: 'bold' }}>Contact our team</Button>
        </Typography>
      </Box>
    </Container>
  );
}
