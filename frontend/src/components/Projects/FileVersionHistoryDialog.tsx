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
  Chip,
  Paper,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  History,
  ExpandMore,
  ExpandLess,
  AccessTime,
  Person,
} from '@mui/icons-material';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';

interface FileVersionHistoryDialogProps {
  open: boolean;
  uploadId: string;
  filePath: string;
  onClose: () => void;
}

interface FileVersion {
  id: number;
  version_number: number;
  content_hash: string;
  scan_id: number | null;
  change_summary: string | null;
  edited_by: string | null;
  created_at: string;
}

interface VersionHistory {
  upload_id: string;
  file_path: string;
  total_versions: number;
  versions: FileVersion[];
}

const FileVersionHistoryDialog: React.FC<FileVersionHistoryDialogProps> = ({
  open,
  uploadId,
  filePath,
  onClose,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<VersionHistory | null>(null);
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null);
  const [versionContent, setVersionContent] = useState<{ [key: number]: string }>({});

  useEffect(() => {
    if (open && uploadId && filePath) {
      fetchVersionHistory();
    }
  }, [open, uploadId, filePath]);

  const fetchVersionHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/history/file-versions/${uploadId}/${filePath}`
      );
      setHistory(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load version history');
    } finally {
      setLoading(false);
    }
  };

  const fetchVersionContent = async (versionId: number) => {
    if (versionContent[versionId]) {
      // Already loaded
      setExpandedVersion(expandedVersion === versionId ? null : versionId);
      return;
    }

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/history/file-version/${versionId}`
      );
      setVersionContent((prev) => ({
        ...prev,
        [versionId]: response.data.content,
      }));
      setExpandedVersion(versionId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load version content');
    }
  };

  const handleToggleVersion = (versionId: number) => {
    if (expandedVersion === versionId) {
      setExpandedVersion(null);
    } else {
      fetchVersionContent(versionId);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <History color="primary" />
          <Typography variant="h6">File Version History</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {filePath}
        </Typography>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        ) : history ? (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Total Versions: {history.total_versions}
            </Typography>
            <Divider sx={{ my: 2 }} />

            <List>
              {history.versions.map((version) => (
                <Paper key={version.id} elevation={1} sx={{ mb: 2 }}>
                  <ListItem
                    button
                    onClick={() => handleToggleVersion(version.id)}
                    sx={{
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                  >
                    <Box display="flex" width="100%" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          label={`Version ${version.version_number}`}
                          color="primary"
                          size="small"
                        />
                        {version.scan_id && (
                          <Chip
                            label={`Scan #${version.scan_id}`}
                            color="secondary"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                      <IconButton size="small">
                        {expandedVersion === version.id ? <ExpandLess /> : <ExpandMore />}
                      </IconButton>
                    </Box>

                    <Box display="flex" gap={2} mt={1} width="100%">
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <AccessTime fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          {formatDistanceToNow(new Date(version.created_at), { addSuffix: true })}
                        </Typography>
                      </Box>

                      {version.edited_by && (
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <Person fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            {version.edited_by}
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    {version.change_summary && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {version.change_summary}
                      </Typography>
                    )}

                    <Collapse in={expandedVersion === version.id} sx={{ width: '100%', mt: 2 }}>
                      {versionContent[version.id] && (
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="caption" color="text.secondary" gutterBottom>
                            Content:
                          </Typography>
                          <Box
                            component="pre"
                            sx={{
                              overflow: 'auto',
                              maxHeight: 300,
                              fontSize: '0.875rem',
                              fontFamily: 'monospace',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                            }}
                          >
                            {versionContent[version.id]}
                          </Box>
                        </Paper>
                      )}
                    </Collapse>
                  </ListItem>
                </Paper>
              ))}
            </List>
          </Box>
        ) : null}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default FileVersionHistoryDialog;
