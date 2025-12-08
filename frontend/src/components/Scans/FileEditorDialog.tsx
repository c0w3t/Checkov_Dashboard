import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, CircularProgress, Alert } from '@mui/material';

interface FileEditorDialogProps {
  open: boolean;
  onClose: () => void;
  fileName: string;
  initialContent: string;
  onSaveAndScan: (content: string) => Promise<{ success: boolean; result?: any; error?: string }>;
}

const FileEditorDialog: React.FC<FileEditorDialogProps> = ({ open, onClose, fileName, initialContent, onSaveAndScan }) => {
  const [content, setContent] = useState(initialContent);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSaveAndScan = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await onSaveAndScan(content);
      if (res.success) {
        setResult(res.result);
      } else {
        setError(res.error || 'Unknown error');
      }
    } catch (e: any) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    setContent(initialContent);
    setResult(null);
    setError(null);
  }, [initialContent, open]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit & Scan: {fileName}</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            rows={18}
            style={{ width: '100%', fontFamily: 'monospace', fontSize: 15, borderRadius: 6, padding: 12, border: '1px solid #e2e8f0', background: '#f9fafb' }}
            spellCheck={false}
          />
        </Box>
        {loading && <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}><CircularProgress /></Box>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {result && (
          <Alert severity={(result.vulnerabilities && result.vulnerabilities.length > 0) || result.failed_checks > 0 ? 'error' : 'success'} sx={{ mb: 2 }}>
            {result.vulnerabilities && result.vulnerabilities.length > 0
              ? `Scan found ${result.vulnerabilities.length} issues.`
              : result.failed_checks > 0
              ? `Scan found ${result.failed_checks} issues.`
              : 'No issues found!'}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="secondary">Close</Button>
        <Button onClick={handleSaveAndScan} variant="contained" color="primary" disabled={loading}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FileEditorDialog;
