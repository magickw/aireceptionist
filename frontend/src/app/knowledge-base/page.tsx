'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  TextField,
  LinearProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Tab,
  Tabs
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  Search,
  Add,
  Description,
  CheckCircle,
  Error as ErrorIcon,
  Pending
} from '@mui/icons-material';
import api from '@/services/api';

interface KnowledgeDocument {
  id: number;
  file_name: string;
  file_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface SearchResult {
  chunk_id: number;
  content: string;
  document_id: number;
  file_name: string;
  similarity: number;
}

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  
  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [textTitle, setTextTitle] = useState('');
  const [textContent, setTextContent] = useState('');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await api.get('/knowledge-base/documents');
      setDocuments(res.data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      await api.post('/knowledge-base/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert('Document uploaded successfully! Processing started.');
      setUploadFile(null);
      fetchDocuments();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!textTitle || !textContent) return;
    
    try {
      setUploading(true);
      await api.post('/knowledge-base/documents/text', {
        title: textTitle,
        content: textContent
      });
      
      alert('Document added successfully! Processing started.');
      setTextTitle('');
      setTextContent('');
      fetchDocuments();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add document');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.delete(`/knowledge-base/documents/${docId}`);
      fetchDocuments();
    } catch (error) {
      alert('Failed to delete document');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    
    try {
      setSearching(true);
      setSearchPerformed(true);
      const res = await api.post('/knowledge-base/search', {
        query: searchQuery,
        top_k: 5
      });
      setSearchResults(res.data.results || []);
    } catch (error) {
      console.error('Search failed', error);
    } finally {
      setSearching(false);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'complete':
        return <Chip icon={<CheckCircle />} label="Ready" color="success" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      case 'indexing':
        return <Chip icon={<CircularProgress size={14} />} label="Processing" color="warning" size="small" />;
      default:
        return <Chip icon={<Pending />} label="Pending" size="small" />;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Knowledge Base
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload documents, FAQs, and policies to give your AI receptionist knowledge about your business.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Documents" />
          <Tab label="Add Content" />
          <Tab label="Search" />
        </Tabs>
      </Box>

      {loading ? (
        <LinearProgress />
      ) : tabValue === 0 ? (
        // Documents Tab
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Your Documents</Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setTabValue(1)}
              >
                Add Document
              </Button>
            </Box>
            
            {documents.length === 0 ? (
              <Alert severity="info">
                No documents yet. Upload your first document to get started!
              </Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>File Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Description fontSize="small" color="primary" />
                            {doc.file_name}
                          </Box>
                        </TableCell>
                        <TableCell>{doc.file_type.toUpperCase()}</TableCell>
                        <TableCell>{getStatusChip(doc.status)}</TableCell>
                        <TableCell>
                          {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '-'}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            color="error"
                            onClick={() => handleDelete(doc.id)}
                            disabled={doc.status === 'indexing'}
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      ) : tabValue === 1 ? (
        // Add Content Tab
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload File
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Supported formats: .txt, .md, .json
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button
                  component="label"
                  variant="outlined"
                  startIcon={<CloudUpload />}
                >
                  Choose File
                  <input
                    type="file"
                    hidden
                    accept=".txt,.md,.json"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />
                </Button>
                {uploadFile && (
                  <Typography variant="body2">{uploadFile.name}</Typography>
                )}
                <Button
                  variant="contained"
                  onClick={handleFileUpload}
                  disabled={!uploadFile || uploading}
                >
                  {uploading ? <CircularProgress size={20} /> : 'Upload'}
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Add Text Content
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Add FAQs, policies, or other text directly.
              </Typography>
              <TextField
                fullWidth
                label="Title"
                value={textTitle}
                onChange={(e) => setTextTitle(e.target.value)}
                sx={{ mb: 2 }}
                placeholder="e.g., FAQ - Pricing"
              />
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Content"
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                sx={{ mb: 2 }}
                placeholder="Enter your content here..."
              />
              <Button
                variant="contained"
                onClick={handleTextSubmit}
                disabled={!textTitle || !textContent || uploading}
              >
                {uploading ? <CircularProgress size={20} /> : 'Add Content'}
              </Button>
            </CardContent>
          </Card>
        </Box>
      ) : (
        // Search Tab
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Semantic Search
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Ask questions and get answers from your knowledge base using AI-powered semantic search.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                fullWidth
                placeholder="e.g., What are your business hours?"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button
                variant="contained"
                startIcon={<Search />}
                onClick={handleSearch}
                disabled={!searchQuery || searching}
              >
                {searching ? <CircularProgress size={20} /> : 'Search'}
              </Button>
            </Box>

            {searching ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : searchPerformed && searchResults.length === 0 ? (
              <Alert severity="info">
                No results found. Try a different query or add more documents to your knowledge base.
              </Alert>
            ) : searchResults.length > 0 ? (
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
                  Found {searchResults.length} relevant results:
                </Typography>
                {searchResults.map((result, index) => (
                  <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle2" color="primary">
                          {result.file_name}
                        </Typography>
                        <Chip
                          label={`${(result.similarity * 100).toFixed(1)}% match`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                      <Typography variant="body2">
                        {result.content}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            ) : searchPerformed === false ? (
              <Alert severity="info">
                Enter a question above to search your knowledge base.
              </Alert>
            ) : null}
          </CardContent>
        </Card>
      )}
    </Container>
  );
}
