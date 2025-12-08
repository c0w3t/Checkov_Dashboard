import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Folder,
  PlayArrow,
  Delete as DeleteIcon,
  InsertDriveFile,
  AccessTime,
} from '@mui/icons-material';
import axios from 'axios';
import FileEditorDialog from '../Scans/FileEditorDialog';
import { fileEditApi } from '../../services/fileEditApi';

interface Upload {
  upload_id: string;
  timestamp: string;
  total_files: number;
  path: string;
  scanned: boolean;
}

interface UploadListDialogProps {
  open: boolean;
  projectId: number;
  projectName: string;
  onClose: () => void;
  onScanStart: (scanId: number) => void;
}

const UploadListDialog: React.FC<UploadListDialogProps> = ({
  open,
  projectId,
  projectName,
  onClose,
  onScanStart,
}) => {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState<string | null>(null);
  // ...existing code...
  const [error, setError] = useState('');

    // File editor dialog state
    const [editorOpen, setEditorOpen] = useState(false);
    const [editorFileName, setEditorFileName] = useState('');
    const [editorFileContent, setEditorFileContent] = useState('');
    const [editorUploadId, setEditorUploadId] = useState<string | null>(null);
    const [editorLoading, setEditorLoading] = useState(false);
  // Open file editor dialog for a file in an upload
  const handleEditFile = async (uploadId: string) => {
    setEditorLoading(true);
    setEditorUploadId(uploadId);
    // For demo, just edit the first file in the upload (real UI should list files)
    // Here, we assume the backend can return the main file path for the upload
    try {
      // Fetch file list for the upload (assume API: /scans/upload/{upload_id}/files)
      const filesResp = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${uploadId}/files`
      );
      const files = filesResp.data.files;
      if (!files || files.length === 0) {
        setError('No files found in this upload.');
        setEditorLoading(false);
        return;
      }
      const filePath = files[0].path; // Pick the first file for now
      setEditorFileName(files[0].name || filePath.split('/').pop() || filePath);
      // Fetch file content
      const contentResp = await fileEditApi.getFileContent(uploadId, filePath);
      setEditorFileContent(contentResp.content);
      setEditorOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load file for editing');
    } finally {
      setEditorLoading(false);
    }
  };

  // Save and scan handler for FileEditorDialog
  const handleSaveAndScan = async (content: string) => {
    if (!editorUploadId || !editorFileName) return { success: false, error: 'No file selected' };
    try {
      // Need the full file path, so re-fetch file list
      const filesResp = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${editorUploadId}/files`
      );
      const files = filesResp.data.files;
      if (!files || files.length === 0) return { success: false, error: 'No files found' };
      const filePath = files[0].path;
      const result = await fileEditApi.updateAndScan(editorUploadId, filePath, content);
      return { success: true, result };
    } catch (err: any) {
      return { success: false, error: err.response?.data?.detail || 'Failed to update and scan' };
    }
  };

  useEffect(() => {
    if (open && projectId) {
      loadUploads();
    }
  }, [open, projectId]);

  const loadUploads = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/uploads/${projectId}`
      );
      setUploads(response.data.uploads);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load uploads');
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async (uploadId: string) => {
    setScanning(uploadId);
    setError('');
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${uploadId}/file/scan`,
        {} // empty body for normal scan
      );
      onScanStart(response.data.id);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scan');
    } finally {
      setScanning(null);
    }
  };

  const handleDelete = async (uploadId: string) => {
    if (!window.confirm('Delete this upload? This cannot be undone.')) {
      return;
    }

    try {
      const parts = uploadId.split('_');
      const timestamp = parts.slice(1).join('_');
      await axios.delete(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${projectId}/${timestamp}`
      );
      loadUploads();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete upload');
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    // Format: 20241124_152249 -> 24/11/2024 15:22:49
    const year = timestamp.substring(0, 4);
    const month = timestamp.substring(4, 6);
    const day = timestamp.substring(6, 8);
    const hour = timestamp.substring(9, 11);
    const minute = timestamp.substring(11, 13);
    const second = timestamp.substring(13, 15);
    return `${day}/${month}/${year} ${hour}:${minute}:${second}`;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Uploaded Files - Ready to Scan
        <Typography variant="body2" color="text.secondary">
          Project: {projectName}
        </Typography>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : uploads.length === 0 ? (
          <Alert severity="info">
            No files uploaded yet. Please upload files first.
          </Alert>
        ) : (
          <>
            <List>
              {uploads.map((upload, index) => (
                <React.Fragment key={upload.upload_id}>
                  {index > 0 && <Divider />}
                  <ListItem
                    secondaryAction={
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          variant="contained"
                          color="primary"
                          size="small"
                          startIcon={scanning === upload.upload_id ? <CircularProgress size={16} /> : <PlayArrow />}
                          onClick={() => handleScan(upload.upload_id)}
                          disabled={scanning === upload.upload_id}
                        >
                          {scanning === upload.upload_id ? 'Starting...' : 'Scan'}
                        </Button>
                        <Button
                          variant="outlined"
                          color="secondary"
                          size="small"
                          onClick={() => handleEditFile(upload.upload_id)}
                          disabled={editorLoading}
                        >
                          Edit
                        </Button>
                        <IconButton
                          edge="end"
                          color="error"
                          onClick={() => handleDelete(upload.upload_id)}
                          disabled={scanning === upload.upload_id}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    }
                  >
                    <ListItemIcon>
                      <Folder color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            Upload {formatTimestamp(upload.timestamp)}
                          </Typography>
                          {upload.scanned && (
                            <Chip label="Scanned" size="small" color="success" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <InsertDriveFile fontSize="small" />
                            <Typography variant="body2">
                              {upload.total_files} files
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <AccessTime fontSize="small" />
                            <Typography variant="body2" color="text.secondary">
                              {upload.upload_id}
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
            {/* File Editor Dialog */}
            <FileEditorDialog
              open={editorOpen}
              onClose={() => setEditorOpen(false)}
              fileName={editorFileName}
              initialContent={editorFileContent}
              onSaveAndScan={handleSaveAndScan}
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default UploadListDialog;
