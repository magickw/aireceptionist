import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle,
  Error,
  PlayArrow,
  Schedule,
  AutoAwesome,
  SmartToy,
  Extension
} from '@mui/icons-material';

interface AutomationStep {
  step_id: number;
  action: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

interface AutomationWorkflow {
  workflow_id: string;
  name: string;
  description: string;
  steps: AutomationStep[];
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  current_step: number;
  total_steps: number;
  progress_percent: number;
}

interface AutomationProgressProps {
  workflow: AutomationWorkflow | null;
  compact?: boolean;
}

const AutomationProgress: React.FC<AutomationProgressProps> = ({ workflow, compact = false }) => {
  const [activeStep, setActiveStep] = useState(-1);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'in_progress':
        return <CircularProgress size={20} />;
      default:
        return <Schedule color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'primary';
      default:
        return 'default';
    }
  };

  if (!workflow) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <AutoAwesome sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          No automation workflow in progress
        </Typography>
      </Box>
    );
  }

  if (compact) {
    return (
      <Card>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Extension sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="subtitle2" fontWeight="bold">
              {workflow.name}
            </Typography>
            <Chip
              label={workflow.status}
              size="small"
              color={getStatusColor(workflow.status) as any}
              sx={{ ml: 'auto' }}
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={workflow.progress_percent}
            sx={{ mb: 1 }}
          />
          <Typography variant="caption" color="text.secondary">
            {workflow.current_step + 1} / {workflow.total_steps} steps
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              bgcolor: 'primary.light',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: 2
            }}
          >
            <SmartToy sx={{ color: 'primary.main' }} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight="bold">
              {workflow.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {workflow.description}
            </Typography>
          </Box>
          <Chip
            label={workflow.status.toUpperCase()}
            size="small"
            color={getStatusColor(workflow.status) as any}
          />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Progress
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {workflow.progress_percent}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={workflow.progress_percent}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {workflow.status === 'failed' && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Automation failed. Some steps were not completed.
            </Typography>
          </Alert>
        )}

        {workflow.status === 'completed' && (
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Automation completed successfully! All {workflow.total_steps} steps executed.
            </Typography>
          </Alert>
        )}

        <Stepper activeStep={workflow.current_step} orientation="vertical">
          {workflow.steps.map((step, index) => (
            <Step key={step.step_id} completed={step.status === 'completed'}>
              <StepLabel
                StepIconComponent={() => getStatusIcon(step.status)}
                error={step.status === 'failed'}
              >
                <Typography variant="body2" fontWeight="medium">
                  {step.description}
                </Typography>
                {step.action && (
                  <Chip
                    label={step.action}
                    size="small"
                    variant="outlined"
                    sx={{ ml: 1, fontSize: '0.7rem', height: 20 }}
                  />
                )}
              </StepLabel>
              <StepContent>
                {step.status === 'in_progress' && (
                  <Box sx={{ py: 2 }}>
                    <CircularProgress size={20} sx={{ mb: 1 }} />
                    <Typography variant="caption" color="text.secondary">
                      Executing...
                    </Typography>
                  </Box>
                )}
                {step.status === 'completed' && step.result && (
                  <Box sx={{ py: 1 }}>
                    <Typography variant="caption" color="success.main">
                      ✓ Completed
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      {JSON.stringify(step.result)}
                    </Typography>
                  </Box>
                )}
                {step.status === 'failed' && step.error && (
                  <Box sx={{ py: 1 }}>
                    <Typography variant="caption" color="error.main">
                      ✗ Failed
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      {step.error}
                    </Typography>
                  </Box>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </CardContent>
    </Card>
  );
};

export default AutomationProgress;