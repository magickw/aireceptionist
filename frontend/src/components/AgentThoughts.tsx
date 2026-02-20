import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Divider,
  Stack
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PsychologyIcon from '@mui/icons-material/Psychology';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SpeedIcon from '@mui/icons-material/Speed';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import api from '@/services/api';

interface Thought {
  step: string;
  message: string;
  timestamp: Date;
}

interface ReasoningChain {
  step: number;
  title: string;
  description: string;
  confidence?: number;
  details?: Record<string, any>;
  context?: Record<string, any>;
  reasoning?: string;
  risk_level?: string;
  alert?: boolean;
  recommendation?: string;
  error?: boolean;
}

interface ReasoningData {
  intent: string;
  confidence: number;
  entities: Record<string, any>;
  selected_action: string;
  action_reasoning: string;
  sentiment: string;
  escalation_risk: number;
  reasoning_chain: ReasoningChain[];
}

interface AgentThoughtsProps {
  thoughts: Thought[];
  reasoningData?: ReasoningData | null;
}

const AgentThoughts: React.FC<AgentThoughtsProps> = ({ thoughts, reasoningData }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await api.post('/approvals/override', {
        request_type: reasoningData?.selected_action,
        call_session_id: reasoningData?.context?.call_session_id,
        original_response: reasoningData?.suggested_response,
        context: reasoningData
      });
      alert('Override approved');
    } catch (error) {
      console.error('Failed to approve:', error);
      alert('Failed to approve');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    setIsProcessing(true);
    try {
      await api.post('/approvals/reject', {
        request_type: reasoningData?.selected_action,
        call_session_id: reasoningData?.context?.call_session_id,
        context: reasoningData
      });
      alert('Action rejected');
    } catch (error) {
      console.error('Failed to reject:', error);
      alert('Failed to reject');
    } finally {
      setIsProcessing(false);
    }
  };
  const [activeStep, setActiveStep] = useState<number>(-1);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.5) return 'warning';
    return 'error';
  };

  const getRiskColor = (risk: number) => {
    if (risk >= 0.7) return 'error';
    if (risk >= 0.3) return 'warning';
    return 'success';
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'negative':
        return <WarningIcon color="error" fontSize="small" />;
      default:
        return <PsychologyIcon color="info" fontSize="small" />;
    }
  };

  return (
    <Box
      sx={{
        bgcolor: '#0f172a',
        color: '#e2e8f0',
        p: 2,
        borderRadius: 2,
        fontFamily: 'monospace',
        fontSize: '0.875rem',
        border: '1px solid #334155',
        height: 500,
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, pb: 2, borderBottom: '1px solid #334155' }}>
        <SmartToyIcon sx={{ mr: 1, color: '#60a5fa' }} />
        <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#94a3b8', fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Nova 2 Lite Reasoning Engine
        </Typography>
      </Box>

      {/* Basic Thoughts (Legacy) */}
      {thoughts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.7rem', textTransform: 'uppercase', mb: 1, display: 'block' }}>
            Processing Log
          </Typography>
          {thoughts.map((thought, index) => (
            <Box key={index} sx={{ mb: 1.5, pl: 2, borderLeft: '2px solid #60a5fa' }}>
              <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.75rem' }}>
                [{thought.timestamp.toLocaleTimeString()}]
              </Typography>{' '}
              <Typography variant="caption" sx={{ color: '#60a5fa', fontWeight: 'bold', fontSize: '0.75rem' }}>
                {thought.step.replace('_', ' ').toUpperCase()}
              </Typography>
              <Typography variant="body2" sx={{ color: '#e2e8f0', fontSize: '0.8rem' }}>
                {thought.message}
              </Typography>
            </Box>
          ))}
        </Box>
      )}

      {/* Rich Reasoning Data */}
      {reasoningData && (
        <Box>
          {/* Human Intervention Alert */}
          {reasoningData.selected_action === 'HUMAN_INTERVENTION' && (
            <Alert 
              severity="error" 
              variant="filled" 
              sx={{ mb: 3, border: '1px solid #ef4444', bgcolor: 'rgba(239, 68, 68, 0.1)', color: '#fca5a5' }}
              icon={<WarningIcon fontSize="inherit" />}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: '#fca5a5' }}>
                SAFETY GATE TRIGGERED
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem', mt: 0.5, color: '#fca5a5' }}>
                {reasoningData.action_reasoning?.split('SAFETY TRIGGER:')[1] || reasoningData.action_reasoning}
              </Typography>
              <Box sx={{ mt: 1.5, display: 'flex', gap: 1 }}>
                <Chip 
                  label="APPROVE OVERRIDE" 
                  size="small" 
                  color="success" 
                  clickable 
                  onClick={handleApprove}
                  sx={{ fontWeight: 'bold' }} 
                />
                <Chip 
                  label="REJECT & TAKE OVER" 
                  size="small" 
                  color="error" 
                  clickable 
                  onClick={handleReject}
                  sx={{ fontWeight: 'bold' }} 
                />
              </Box>
            </Alert>
          )}

          {/* Summary Cards */}
          <Stack spacing={1.5} sx={{ mb: 3 }}>
            {/* Intent Card */}
            <Box sx={{ bgcolor: '#1e293b', p: 2, borderRadius: 1, border: '1px solid #334155' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <PsychologyIcon fontSize="inherit" /> Detected Intent
              </Typography>
              <Typography variant="body2" sx={{ color: '#fff', fontWeight: 'bold', fontSize: '0.9rem', mt: 0.5 }}>
                {reasoningData.intent}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={reasoningData.confidence * 100}
                  sx={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#334155' }}
                  color={getConfidenceColor(reasoningData.confidence) as any}
                />
                <Chip
                  label={`${(reasoningData.confidence * 100).toFixed(0)}%`}
                  size="small"
                  color={getConfidenceColor(reasoningData.confidence) as any}
                  sx={{ height: 20, fontSize: '0.7rem', minWidth: 45 }}
                />
              </Box>
            </Box>

            {/* Action Card */}
            <Box sx={{ bgcolor: '#1e293b', p: 2, borderRadius: 1, border: '1px solid #334155' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <SpeedIcon fontSize="inherit" /> Selected Action
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                <Chip
                  label={reasoningData.selected_action}
                  color="primary"
                  size="small"
                  sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}
                />
              </Box>
              <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.75rem', mt: 1, display: 'block', fontStyle: 'italic' }}>
                {reasoningData.action_reasoning}
              </Typography>
            </Box>

            {/* Sentiment & Risk */}
            <Box sx={{ display: 'flex', gap: 1.5 }}>
              <Box sx={{ flex: 1, bgcolor: '#1e293b', p: 2, borderRadius: 1, border: '1px solid #334155' }}>
                <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {getSentimentIcon(reasoningData.sentiment)} Sentiment
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff', fontWeight: 'bold', fontSize: '0.9rem', mt: 0.5, textTransform: 'capitalize' }}>
                  {reasoningData.sentiment}
                </Typography>
              </Box>
              <Box sx={{ flex: 1, bgcolor: '#1e293b', p: 2, borderRadius: 1, border: '1px solid #334155' }}>
                <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <TrendingUpIcon fontSize="inherit" /> Escalation Risk
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <LinearProgress
                    variant="determinate"
                    value={reasoningData.escalation_risk * 100}
                    sx={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#334155' }}
                    color={getRiskColor(reasoningData.escalation_risk) as any}
                  />
                  <Chip
                    label={`${(reasoningData.escalation_risk * 100).toFixed(0)}%`}
                    size="small"
                    color={getRiskColor(reasoningData.escalation_risk) as any}
                    sx={{ height: 20, fontSize: '0.7rem', minWidth: 45 }}
                  />
                </Box>
              </Box>
            </Box>
          </Stack>

          {/* Entities */}
          {reasoningData.entities && Object.keys(reasoningData.entities).length > 0 && (
            <Box sx={{ mb: 3, bgcolor: '#1e293b', p: 2, borderRadius: 1, border: '1px solid #334155' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', mb: 1, display: 'block' }}>
                Extracted Entities
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap">
                {Object.entries(reasoningData.entities).map(([key, value]) => (
                  value && (
                    <Chip
                      key={key}
                      label={`${key}: ${value}`}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 22, borderColor: '#475569', color: '#cbd5e1' }}
                    />
                  )
                ))}
              </Stack>
            </Box>
          )}

          {/* Reasoning Chain */}
          <Box>
            <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', mb: 1.5, display: 'block' }}>
              Reasoning Chain
            </Typography>
            {reasoningData.reasoning_chain && reasoningData.reasoning_chain.map((step, index) => (
              <Accordion
                key={index}
                expanded={activeStep === index}
                onChange={() => setActiveStep(activeStep === index ? -1 : index)}
                sx={{
                  mb: 1,
                  bgcolor: step.alert ? '#1e293b' : '#1e293b',
                  border: step.alert ? '1px solid #ef4444' : '1px solid #334155',
                  borderRadius: 1,
                  '&:before': { display: 'none' },
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon sx={{ color: '#94a3b8', fontSize: '1rem' }} />}
                  sx={{
                    minHeight: 48,
                    '& .MuiAccordionSummary-content': {
                      margin: '12px 0',
                    }
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                    <Box
                      sx={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        bgcolor: step.error ? '#ef4444' : step.alert ? '#f59e0b' : '#60a5fa',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        color: '#fff'
                      }}
                    >
                      {step.step}
                    </Box>
                    <Typography variant="body2" sx={{ color: '#e2e8f0', fontSize: '0.85rem', fontWeight: step.alert ? 'bold' : 'normal' }}>
                      {step.title}
                    </Typography>
                    {step.confidence && (
                      <Chip
                        label={`${(step.confidence * 100).toFixed(0)}%`}
                        size="small"
                        color={getConfidenceColor(step.confidence) as any}
                        sx={{ height: 20, fontSize: '0.7rem', minWidth: 45 }}
                      />
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ pt: 1, pb: 1 }}>
                  <Typography variant="body2" sx={{ color: '#94a3b8', fontSize: '0.8rem', mb: 1.5 }}>
                    {step.description}
                  </Typography>

                  {step.reasoning && (
                    <Box sx={{ mb: 1.5, p: 1.5, bgcolor: '#0f172a', borderRadius: 1, borderLeft: '2px solid #60a5fa' }}>
                      <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', display: 'block', mb: 0.5 }}>
                        Reasoning
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#e2e8f0', fontSize: '0.8rem' }}>
                        {step.reasoning}
                      </Typography>
                    </Box>
                  )}

                  {step.details && Object.keys(step.details).length > 0 && (
                    <Box sx={{ mb: 1.5 }}>
                      <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', display: 'block', mb: 0.5 }}>
                        Details
                      </Typography>
                      <Stack spacing={0.5}>
                        {Object.entries(step.details).map(([key, value]) => (
                          value && (
                            <Typography key={key} variant="body2" sx={{ color: '#cbd5e1', fontSize: '0.8rem' }}>
                              <span style={{ color: '#94a3b8' }}>{key}:</span> {String(value)}
                            </Typography>
                          )
                        ))}
                      </Stack>
                    </Box>
                  )}

                  {step.recommendation && (
                    <Alert severity="warning" sx={{ fontSize: '0.8rem', py: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Recommendation:</strong> {step.recommendation}
                      </Typography>
                    </Alert>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </Box>
      )}

      {/* Pulse indicator */}
      {(thoughts.length > 0 || reasoningData) && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, pt: 2, borderTop: '1px solid #334155' }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#22c55e', animation: 'pulse 1.5s infinite' }} />
          <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.7rem' }}>
            Nova 2 Lite Active
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default AgentThoughts;
