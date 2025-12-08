import React, { useEffect, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, Typography, List, ListItem, ListItemText, Alert } from '@mui/material';
import axios from 'axios';

interface FileVersionHistoryProps {
  open: boolean;
  onClose: () => void;
  uploadId: string;
  filePath: string; // relative
  vulnerabilityId?: number; // optional for seeding original
}

interface FileVersionItem {
  id: number;
  version_number: number;
  content_hash: string;
  scan_id?: number;
  change_summary?: string;
  edited_by?: string;
  created_at: string;
}

const API_BASE_URL = 'http://localhost:8000/api/history';

const FileVersionHistory: React.FC<FileVersionHistoryProps> = ({ open, onClose, uploadId, filePath, vulnerabilityId }) => {
  const [versions, setVersions] = useState<FileVersionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [restoreMsg, setRestoreMsg] = useState<string | null>(null);
  const [seedMsg, setSeedMsg] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setError(null);
      try {
        const resp = await axios.get(`${API_BASE_URL}/file-versions/${encodeURIComponent(uploadId)}/${encodeURIComponent(filePath)}`);
        setVersions(resp.data.versions || []);
      } catch (e1: any) {
        // Fallback: try by-file endpoint
        try {
          const resp2 = await axios.get(`${API_BASE_URL}/file-versions/by-file`, { params: { file_path: filePath } });
          setVersions(resp2.data.versions || []);
        } catch (e2: any) {
          setError(e2.response?.data?.detail || e1.response?.data?.detail || 'Failed to load version history');
        }
      }
    };
    if (open) load();
  }, [open, uploadId, filePath]);

  const handleRestore = async (versionId: number) => {
    setError(null);
    setRestoreMsg(null);
    try {
      const resp = await axios.post(`${API_BASE_URL}/file-versions/restore`, { version_id: versionId });
      if (resp.data && resp.data.success) {
        setRestoreMsg(`Restored to ${resp.data.file_path}`);
      } else {
        setError(resp.data?.error || 'Failed to restore');
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to restore');
    }
  };

  const handleRecordOriginal = async () => {
    if (!vulnerabilityId) return;
    setError(null);
    setSeedMsg(null);
    try {
      const resp = await axios.post(`${API_BASE_URL}/file-versions/record-original`, { vulnerability_id: vulnerabilityId });
      setSeedMsg('Original content recorded.');
      // Reload list
      const respList = await axios.get(`${API_BASE_URL}/file-versions/by-file`, { params: { file_path: filePath } });
      setVersions(respList.data.versions || []);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to record original');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>File Version History</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2">Upload: {uploadId}</Typography>
          <Typography variant="body2">File: {filePath}</Typography>
        </Box>
        {error && <Alert severity="error">{error}</Alert>}
        {restoreMsg && <Alert severity="success" sx={{ mb: 2 }}>{restoreMsg}</Alert>}
        {seedMsg && <Alert severity="success" sx={{ mb: 2 }}>{seedMsg}</Alert>}
        <List>
          {versions.map((v) => (
            <ListItem key={v.id} sx={{ borderBottom: '1px solid #eee' }}>
              <ListItemText
                primary={`v${v.version_number} • ${new Date(v.created_at).toLocaleString()}`}
                secondary={`hash: ${v.content_hash}${v.change_summary ? ' • ' + v.change_summary : ''}`}
              />
              <Button size="small" onClick={() => handleRestore(v.id)}>Restore</Button>
            </ListItem>
          ))}
          {versions.length === 0 && !error && (
            <Box>
              <Typography variant="body2" sx={{ mb: 1 }}>No versions recorded yet.</Typography>
              {vulnerabilityId && (
                <Button size="small" variant="outlined" onClick={handleRecordOriginal}>Record Original</Button>
              )}
            </Box>
          )}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default FileVersionHistory;
