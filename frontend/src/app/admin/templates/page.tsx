"use client";

import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  History,
  Refresh,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';

interface BusinessTemplate {
  id: number;
  template_key: string;
  name: string;
  icon: string;
  description: string;
  autonomy_level: string;
  risk_profile: {
    high_risk_intents: string[];
    auto_escalate_threshold: number;
    confidence_threshold: number;
  };
  common_intents: string[];
  fields: Record<string, any>;
  booking_flow: Record<string, any>;
  system_prompt_addition: string;
  example_responses: Record<string, string>;
  is_active: boolean;
  is_default: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

function TabPanel({ children, value, index }: { children: React.ReactNode; value: number; index: number }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function BusinessTemplatesPage() {
  const [templates, setTemplates] = useState<BusinessTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<BusinessTemplate | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState<Partial<BusinessTemplate>>({});
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/admin/templates/');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      setError('Failed to fetch templates');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setFormData({
      autonomy_level: 'MEDIUM',
      risk_profile: {
        high_risk_intents: [],
        auto_escalate_threshold: 0.5,
        confidence_threshold: 0.6,
      },
      common_intents: [],
      fields: {},
      booking_flow: {},
      example_responses: {},
      is_active: true,
      is_default: false,
    });
    setIsCreating(true);
    setIsEditing(true);
  };

  const handleEdit = (template: BusinessTemplate) => {
    setSelectedTemplate(template);
    setFormData(template);
    setIsCreating(false);
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      const url = isCreating
        ? '/api/v1/admin/templates/'
        : `/api/v1/admin/templates/${formData.id}`;
      
      const method = isCreating ? 'POST' : 'PUT';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsEditing(false);
        fetchTemplates();
      } else {
        setError('Failed to save template');
      }
    } catch (err) {
      setError('Failed to save template');
      console.error('Error:', err);
    }
  };

  const handleDelete = async (templateId: number) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    
    try {
      const response = await fetch(`/api/v1/admin/templates/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchTemplates();
      } else {
        setError('Failed to delete template');
      }
    } catch (err) {
      setError('Failed to delete template');
      console.error('Error:', err);
    }
  };

  const clearCache = async () => {
    try {
      const response = await fetch('/api/v1/admin/templates/cache/clear', {
        method: 'POST',
      });

      if (response.ok) {
        alert('Cache cleared successfully');
      } else {
        setError('Failed to clear cache');
      }
    } catch (err) {
      setError('Failed to clear cache');
      console.error('Error:', err);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 8 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={6}>
        <Box>
          <Typography variant="h3" gutterBottom>
            Business Templates
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage AI agent templates for different business types
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button variant="outlined" onClick={clearCache} startIcon={<Refresh />}>
            Clear Cache
          </Button>
          <Button variant="contained" onClick={handleCreate} startIcon={<Add />}>
            Create Template
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {isEditing ? (
        <TemplateEditor
          template={formData}
          isCreating={isCreating}
          onSave={handleSave}
          onCancel={() => setIsEditing(false)}
          onChange={setFormData}
        />
      ) : (
        <Box display="flex" flexDirection="column" gap={3}>
          {templates.map((template) => (
            <Card key={template.id}>
              <CardContent sx={{ pt: 3 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Box display="flex" alignItems="flex-start" gap={2}>
                    <Paper sx={{ p: 1.5, bgcolor: 'primary.10', borderRadius: 1 }}>
                      <Typography variant="h4">{template.icon}</Typography>
                    </Paper>
                    <Box>
                      <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                        <Typography variant="h6">{template.name}</Typography>
                        {template.is_default && (
                          <Chip label="Default" size="small" color="secondary" />
                        )}
                        {template.is_active ? (
                          <Chip
                            label="Active"
                            size="small"
                            color="success"
                            icon={<CheckCircle />}
                          />
                        ) : (
                          <Chip
                            label="Inactive"
                            size="small"
                            color="default"
                            icon={<Cancel />}
                          />
                        )}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {template.description} • Version {template.version}
                      </Typography>
                    </Box>
                  </Box>
                  <Box display="flex" gap={1}>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<History />}
                      onClick={() => setSelectedTemplate(template)}
                    >
                      Versions
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<Edit />}
                      onClick={() => handleEdit(template)}
                    >
                      Edit
                    </Button>
                    {!template.is_default && (
                      <Button
                        variant="outlined"
                        size="small"
                        color="error"
                        startIcon={<Delete />}
                        onClick={() => handleDelete(template.id)}
                      >
                        Delete
                      </Button>
                    )}
                  </Box>
                </Box>

                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                  <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                    <Tab label="Overview" />
                    <Tab label="Fields" />
                    <Tab label="Booking Flow" />
                    <Tab label="Prompts" />
                  </Tabs>
                </Box>

                <TabPanel value={tabValue} index={0}>
                  <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2} mb={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Template Key</Typography>
                      <Typography variant="body2">{template.template_key}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Autonomy Level</Typography>
                      <Chip
                        label={template.autonomy_level}
                        size="small"
                        color={
                          template.autonomy_level === 'HIGH'
                            ? 'success'
                            : template.autonomy_level === 'RESTRICTED'
                            ? 'error'
                            : 'primary'
                        }
                      />
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Confidence Threshold</Typography>
                      <Typography variant="body2">{template.risk_profile.confidence_threshold}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Auto-Escalate Threshold</Typography>
                      <Typography variant="body2">{template.risk_profile.auto_escalate_threshold}</Typography>
                    </Box>
                  </Box>
                  <Box mb={2}>
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      Common Intents
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {template.common_intents.map((intent) => (
                        <Chip key={intent} label={intent} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      High-Risk Intents
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {template.risk_profile.high_risk_intents.map((intent) => (
                        <Chip key={intent} label={intent} size="small" color="error" />
                      ))}
                    </Box>
                  </Box>
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.100', overflow: 'auto', maxHeight: 400 }}>
                    <pre style={{ fontSize: 12 }}>
                      {JSON.stringify(template.fields, null, 2)}
                    </pre>
                  </Paper>
                </TabPanel>

                <TabPanel value={tabValue} index={2}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.100', overflow: 'auto', maxHeight: 400 }}>
                    <pre style={{ fontSize: 12 }}>
                      {JSON.stringify(template.booking_flow, null, 2)}
                    </pre>
                  </Paper>
                </TabPanel>

                <TabPanel value={tabValue} index={3}>
                  <Box display="flex" flexDirection="column" gap={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        System Prompt Addition
                      </Typography>
                      <TextField
                        fullWidth
                        multiline
                        rows={8}
                        value={template.system_prompt_addition}
                        InputProps={{ readOnly: true }}
                      />
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        Example Responses
                      </Typography>
                      <Paper sx={{ p: 2, bgcolor: 'grey.100', overflow: 'auto', maxHeight: 400 }}>
                        <pre style={{ fontSize: 12 }}>
                          {JSON.stringify(template.example_responses, null, 2)}
                        </pre>
                      </Paper>
                    </Box>
                  </Box>
                </TabPanel>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Container>
  );
}

function TemplateEditor({
  template,
  isCreating,
  onSave,
  onCancel,
  onChange,
}: {
  template: Partial<BusinessTemplate>;
  isCreating: boolean;
  onSave: () => void;
  onCancel: () => void;
  onChange: (template: Partial<BusinessTemplate>) => void;
}) {
  return (
    <Card>
      <CardContent sx={{ pt: 4 }}>
        <Typography variant="h6" gutterBottom>
          {isCreating ? 'Create New Template' : 'Edit Template'}
        </Typography>
        <Box display="flex" flexDirection="column" gap={3}>
          <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2}>
            <Box>
              <TextField
                fullWidth
                label="Template Key"
                value={template.template_key || ''}
                onChange={(e) => onChange({ ...template, template_key: e.target.value })}
                disabled={!isCreating}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="Name"
                value={template.name || ''}
                onChange={(e) => onChange({ ...template, name: e.target.value })}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="Icon"
                value={template.icon || ''}
                onChange={(e) => onChange({ ...template, icon: e.target.value })}
              />
            </Box>
            <FormControl fullWidth>
              <InputLabel>Autonomy Level</InputLabel>
              <Select
                value={template.autonomy_level || 'MEDIUM'}
                label="Autonomy Level"
                onChange={(e) => onChange({ ...template, autonomy_level: e.target.value })}
              >
                <MenuItem value="HIGH">High</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="RESTRICTED">Restricted</MenuItem>
              </Select>
            </FormControl>
          </Box>
          <Box>
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={3}
              value={template.description || ''}
              onChange={(e) => onChange({ ...template, description: e.target.value })}
            />
          </Box>
          <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2}>
            <Box>
              <TextField
                fullWidth
                label="Confidence Threshold"
                type="number"
                inputProps={{ step: 0.1, min: 0, max: 1 }}
                value={template.risk_profile?.confidence_threshold || 0.6}
                onChange={(e) => onChange({
                  ...template,
                  risk_profile: {
                    ...template.risk_profile,
                    confidence_threshold: parseFloat(e.target.value),
                  },
                })}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="Auto-Escalate Threshold"
                type="number"
                inputProps={{ step: 0.1, min: 0, max: 1 }}
                value={template.risk_profile?.auto_escalate_threshold || 0.5}
                onChange={(e) => onChange({
                  ...template,
                  risk_profile: {
                    ...template.risk_profile,
                    auto_escalate_threshold: parseFloat(e.target.value),
                  },
                })}
              />
            </Box>
          </Box>
          <Box>
            <TextField
              fullWidth
              label="System Prompt Addition"
              multiline
              rows={6}
              value={template.system_prompt_addition || ''}
              onChange={(e) => onChange({ ...template, system_prompt_addition: e.target.value })}
            />
          </Box>
          <Box display="flex" justifyContent="flex-end" gap={2}>
            <Button variant="outlined" onClick={onCancel}>
              Cancel
            </Button>
            <Button variant="contained" onClick={onSave}>
              Save Template
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}