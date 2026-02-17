"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Edit, Trash2, History, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

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

export default function BusinessTemplatesPage() {
  const [templates, setTemplates] = useState<BusinessTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<BusinessTemplate | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  const [formData, setFormData] = useState<Partial<BusinessTemplate>>({});

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
    } catch (error) {
      console.error('Error fetching templates:', error);
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
      }
    } catch (error) {
      console.error('Error saving template:', error);
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
      }
    } catch (error) {
      console.error('Error deleting template:', error);
    }
  };

  const handleRestoreVersion = async (versionId: number) => {
    if (!confirm('Are you sure you want to restore this version?')) return;
    
    try {
      const response = await fetch(`/api/v1/admin/templates/${selectedTemplate?.id}/versions/${versionId}/restore`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchTemplates();
        setShowVersions(false);
      }
    } catch (error) {
      console.error('Error restoring version:', error);
    }
  };

  const clearCache = async () => {
    try {
      const response = await fetch('/api/v1/admin/templates/cache/clear', {
        method: 'POST',
      });

      if (response.ok) {
        alert('Cache cleared successfully');
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="animate-spin h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Business Templates</h1>
          <p className="text-muted-foreground">Manage AI agent templates for different business types</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={clearCache}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Clear Cache
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Create Template
          </Button>
        </div>
      </div>

      {isEditing ? (
        <TemplateEditor
          template={formData}
          isCreating={isCreating}
          onSave={handleSave}
          onCancel={() => setIsEditing(false)}
          onChange={setFormData}
        />
      ) : (
        <div className="grid gap-6">
          {templates.map((template) => (
            <Card key={template.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <span className="text-2xl">{template.icon}</span>
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {template.name}
                        {template.is_default && (
                          <Badge variant="secondary">Default</Badge>
                        )}
                        {template.is_active ? (
                          <Badge variant="default" className="bg-green-500">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="outline">
                            <XCircle className="h-3 w-3 mr-1" />
                            Inactive
                          </Badge>
                        )}
                      </CardTitle>
                      <CardDescription>
                        {template.description} • Version {template.version}
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => setSelectedTemplate(template)}>
                          <History className="h-4 w-4 mr-2" />
                          Versions
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Version History</DialogTitle>
                          <DialogDescription>
                            View and restore previous versions of this template
                          </DialogDescription>
                        </DialogHeader>
                        <VersionHistory
                          templateId={template.id}
                          onRestore={handleRestoreVersion}
                        />
                      </DialogContent>
                    </Dialog>
                    <Button variant="outline" size="sm" onClick={() => handleEdit(template)}>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    {!template.is_default && (
                      <Button variant="destructive" size="sm" onClick={() => handleDelete(template.id)}>
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="overview" className="w-full">
                  <TabsList>
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="fields">Fields</TabsTrigger>
                    <TabsTrigger value="flow">Booking Flow</TabsTrigger>
                    <TabsTrigger value="prompts">Prompts</TabsTrigger>
                  </TabsList>
                  <TabsContent value="overview" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Template Key</Label>
                        <p className="text-sm text-muted-foreground">{template.template_key}</p>
                      </div>
                      <div>
                        <Label>Autonomy Level</Label>
                        <Badge variant={template.autonomy_level === 'HIGH' ? 'default' : template.autonomy_level === 'RESTRICTED' ? 'destructive' : 'secondary'}>
                          {template.autonomy_level}
                        </Badge>
                      </div>
                      <div>
                        <Label>Confidence Threshold</Label>
                        <p className="text-sm text-muted-foreground">{template.risk_profile.confidence_threshold}</p>
                      </div>
                      <div>
                        <Label>Auto-Escalate Threshold</Label>
                        <p className="text-sm text-muted-foreground">{template.risk_profile.auto_escalate_threshold}</p>
                      </div>
                    </div>
                    <div>
                      <Label>Common Intents</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {template.common_intents.map((intent) => (
                          <Badge key={intent} variant="outline">{intent}</Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Label>High-Risk Intents</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {template.risk_profile.high_risk_intents.map((intent) => (
                          <Badge key={intent} variant="destructive">{intent}</Badge>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                  <TabsContent value="fields">
                    <pre className="text-xs bg-muted p-4 rounded-lg overflow-auto">
                      {JSON.stringify(template.fields, null, 2)}
                    </pre>
                  </TabsContent>
                  <TabsContent value="flow">
                    <pre className="text-xs bg-muted p-4 rounded-lg overflow-auto">
                      {JSON.stringify(template.booking_flow, null, 2)}
                    </pre>
                  </TabsContent>
                  <TabsContent value="prompts">
                    <div className="space-y-4">
                      <div>
                        <Label>System Prompt Addition</Label>
                        <Textarea
                          value={template.system_prompt_addition}
                          readOnly
                          className="mt-2 min-h-[200px]"
                        />
                      </div>
                      <div>
                        <Label>Example Responses</Label>
                        <pre className="text-xs bg-muted p-4 rounded-lg overflow-auto mt-2">
                          {JSON.stringify(template.example_responses, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
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
      <CardHeader>
        <CardTitle>{isCreating ? 'Create New Template' : 'Edit Template'}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="template_key">Template Key</Label>
              <Input
                id="template_key"
                value={template.template_key || ''}
                onChange={(e) => onChange({ ...template, template_key: e.target.value })}
                disabled={!isCreating}
              />
            </div>
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={template.name || ''}
                onChange={(e) => onChange({ ...template, name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="icon">Icon</Label>
              <Input
                id="icon"
                value={template.icon || ''}
                onChange={(e) => onChange({ ...template, icon: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="autonomy_level">Autonomy Level</Label>
              <Select
                value={template.autonomy_level || 'MEDIUM'}
                onValueChange={(value) => onChange({ ...template, autonomy_level: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HIGH">High</SelectItem>
                  <SelectItem value="MEDIUM">Medium</SelectItem>
                  <SelectItem value="RESTRICTED">Restricted</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={template.description || ''}
              onChange={(e) => onChange({ ...template, description: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="confidence_threshold">Confidence Threshold</Label>
              <Input
                id="confidence_threshold"
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={template.risk_profile?.confidence_threshold || 0.6}
                onChange={(e) => onChange({
                  ...template,
                  risk_profile: {
                    ...template.risk_profile,
                    confidence_threshold: parseFloat(e.target.value),
                  },
                })}
              />
            </div>
            <div>
              <Label htmlFor="auto_escalate_threshold">Auto-Escalate Threshold</Label>
              <Input
                id="auto_escalate_threshold"
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={template.risk_profile?.auto_escalate_threshold || 0.5}
                onChange={(e) => onChange({
                  ...template,
                  risk_profile: {
                    ...template.risk_profile,
                    auto_escalate_threshold: parseFloat(e.target.value),
                  },
                })}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="system_prompt_addition">System Prompt Addition</Label>
            <Textarea
              id="system_prompt_addition"
              value={template.system_prompt_addition || ''}
              onChange={(e) => onChange({ ...template, system_prompt_addition: e.target.value })}
              className="min-h-[200px]"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button onClick={onSave}>
              Save Template
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function VersionHistory({
  templateId,
  onRestore,
}: {
  templateId: number;
  onRestore: (versionId: number) => void;
}) {
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVersions();
  }, [templateId]);

  const fetchVersions = async () => {
    try {
      const response = await fetch(`/api/v1/admin/templates/${templateId}/versions`);
      if (response.ok) {
        const data = await response.json();
        setVersions(data);
      }
    } catch (error) {
      console.error('Error fetching versions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading versions...</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Version</TableHead>
          <TableHead>Change Description</TableHead>
          <TableHead>Created At</TableHead>
          <TableHead>Active</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {versions.map((version) => (
          <TableRow key={version.id}>
            <TableCell>{version.version_number}</TableCell>
            <TableCell>{version.change_description || 'No description'}</TableCell>
            <TableCell>{new Date(version.created_at).toLocaleString()}</TableCell>
            <TableCell>
              {version.is_active ? (
                <Badge variant="default">Active</Badge>
              ) : (
                <Badge variant="outline">Inactive</Badge>
              )}
            </TableCell>
            <TableCell>
              {!version.is_active && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRestore(version.id)}
                >
                  Restore
                </Button>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}