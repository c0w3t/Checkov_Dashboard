import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Paper,
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  Folder,
  Delete as DeleteIcon,
  CheckCircle,
} from '@mui/icons-material';
import axios from 'axios';

interface FileUploadDialogProps {
  open: boolean;
  projectId: number;
  projectName: string;
  onClose: () => void;
  onUploadComplete: (uploadId: string, totalFiles: number) => void;
}

const FileUploadDialog: React.FC<FileUploadDialogProps> = ({
  open,
  projectId,
  projectName,
  onClose,
  onUploadComplete,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleDrop = useCallback(async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    const items = Array.from(e.dataTransfer.items);
    const files: File[] = [];

    // Process all dropped items (files and directories)
    for (const item of items) {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry) {
          await processEntry(entry, files);
        }
      }
    }

    setSelectedFiles((prev) => [...prev, ...files]);
    setError('');
  }, []);

  // Recursive function to process directory entries
  const processEntry = async (entry: any, files: File[]): Promise<void> => {
    if (entry.isFile) {
      const file = await new Promise<File>((resolve) => {
        entry.file((f: File) => resolve(f));
      });
      files.push(file);
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      const entries = await new Promise<any[]>((resolve) => {
        reader.readEntries((e: any[]) => resolve(e));
      });

      for (const childEntry of entries) {
        await processEntry(childEntry, files);
      }
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
      setError('');
    }
  };

  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
      setError('');
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError('');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('project_id', projectId.toString());
      
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setUploadProgress(progress);
          },
        }
      );

      setSuccess(true);
      setTimeout(() => {
        onUploadComplete(response.data.upload_id, response.data.total_files);
        handleClose();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setSelectedFiles([]);
      setError('');
      setSuccess(false);
      setUploadProgress(0);
      onClose();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.zip')) return <Folder color="primary" />;
    if (fileName.endsWith('.tf')) return <InsertDriveFile sx={{ color: '#844fba' }} />;
    if (fileName.endsWith('.yaml') || fileName.endsWith('.yml')) return <InsertDriveFile sx={{ color: '#cb171e' }} />;
    if (fileName.toLowerCase().includes('dockerfile')) return <InsertDriveFile sx={{ color: '#2496ed' }} />;
    if (fileName.endsWith('.json')) return <InsertDriveFile sx={{ color: '#f1c40f' }} />;
    return <InsertDriveFile color="action" />;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Upload Files
        <Typography variant="body2" color="text.secondary">
          Project: {projectName}
        </Typography>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 2 }}>
            Files uploaded successfully! You can now scan them.
          </Alert>
        )}

        {/* Drop Zone */}
        <Paper
          variant="outlined"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          sx={{
            p: 4,
            textAlign: 'center',
            bgcolor: 'background.default',
            border: '2px dashed',
            borderColor: 'primary.main',
            mb: 2,
          }}
        >
          <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
          <Typography variant="h6" gutterBottom>
            Drag & Drop Files or Folders Here
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            or choose an option below
          </Typography>

          {/* Hidden inputs */}
          <input
            accept="*"
            style={{ display: 'none' }}
            id="file-upload"
            multiple
            type="file"
            onChange={handleFileSelect}
          />
          <input
            style={{ display: 'none' }}
            id="folder-upload"
            type="file"
            /* @ts-ignore */
            webkitdirectory=""
            directory=""
            multiple
            onChange={handleFolderSelect}
          />

          {/* Buttons */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2 }}>
            <label htmlFor="file-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<InsertDriveFile />}
              >
                Select Files
              </Button>
            </label>
            <label htmlFor="folder-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<Folder />}
              >
                Select Folder
              </Button>
            </label>
          </Box>

          <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
            Supported: .tf, .yaml, .yml, Dockerfile, .json (all IaC frameworks)
          </Typography>
        </Paper>

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Selected Files ({selectedFiles.length})
            </Typography>
            <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
              {selectedFiles.map((file, index) => {
                // Extract relative path if available (from webkitRelativePath)
                const displayPath = (file as any).webkitRelativePath || file.name;

                return (
                  <ListItem
                    key={index}
                    secondaryAction={
                      !uploading && (
                        <IconButton
                          edge="end"
                          onClick={() => handleRemoveFile(index)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      )
                    }
                  >
                    <ListItemIcon>
                      {getFileIcon(file.name)}
                    </ListItemIcon>
                    <ListItemText
                      primary={displayPath}
                      secondary={formatFileSize(file.size)}
                      primaryTypographyProps={{
                        sx: {
                          fontSize: '0.875rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }
                      }}
                    />
                  </ListItem>
                );
              })}
            </List>
          </Box>
        )}

        {/* Upload Progress */}
        {uploading && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Uploading... {uploadProgress}%
            </Typography>
            <LinearProgress variant="determinate" value={uploadProgress} />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={uploading || selectedFiles.length === 0}
          startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FileUploadDialog;
