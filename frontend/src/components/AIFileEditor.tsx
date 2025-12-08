import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import { ContentCopy, Edit, AutoAwesome } from '@mui/icons-material';
import aiService, { EditFileRequest, EditFileResponse } from '../services/aiService';

interface AIFileEditorProps {
  open: boolean;
  onClose: () => void;
  fileContent: string;
  filePath: string;
  onApplyEdit?: (editedContent: string) => void;
}

const AIFileEditor: React.FC<AIFileEditorProps> = ({
  open,
  onClose,
  fileContent,
  filePath,
  onApplyEdit,
}) => {
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editResult, setEditResult] = useState<EditFileResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleEdit = async () => {
    if (!instruction.trim()) {
      setError('Please provide editing instructions');
      return;
    }

    setLoading(true);
    setError(null);
    setEditResult(null);

    const request: EditFileRequest = {
      file_content: fileContent,
      file_path: filePath,
      user_instruction: instruction,
    };

    try {
      const result = await aiService.editFile(request);
      setEditResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to edit file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (editResult) {
      navigator.clipboard.writeText(editResult.edited_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleApply = () => {
    if (editResult && onApplyEdit) {
      onApplyEdit(editResult.edited_code);
      handleClose();
    }
  };

  const handleClose = () => {
    setInstruction('');
    setEditResult(null);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoAwesome color="primary" />
        AI File Editor
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              File:
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {filePath}
            </Typography>
          </Box>

          <TextField
            label="What would you like to change?"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            fullWidth
            required
            multiline
            rows={3}
            placeholder="e.g., Add error handling, Update the timeout to 30 seconds, Refactor to use async/await..."
          />

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>AI is editing your file...</Typography>
            </Box>
          )}

          {editResult && (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                <Typography variant="body2" fontWeight="bold">
                  {editResult.explanation}
                </Typography>
              </Alert>

              <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
                Changes Made:
              </Typography>
              <Box sx={{ mb: 2 }}>
                {editResult.changes_made.map((change, index) => (
                  <Chip
                    key={index}
                    label={change}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  Original Code:
                </Typography>
              </Box>
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5', maxHeight: 200, overflow: 'auto', mb: 2 }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.85rem' }}>
                  {editResult.original_code}
                </pre>
              </Paper>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  Edited Code:
                </Typography>
                <Tooltip title={copied ? 'Copied!' : 'Copy edited code'}>
                  <IconButton onClick={handleCopyCode} size="small">
                    <ContentCopy />
                  </IconButton>
                </Tooltip>
              </Box>
              <Paper sx={{ p: 2, bgcolor: '#e3f2fd', maxHeight: 200, overflow: 'auto' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.85rem' }}>
                  {editResult.edited_code}
                </pre>
              </Paper>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        {!editResult && (
          <Button
            onClick={handleEdit}
            variant="contained"
            disabled={loading || !instruction.trim()}
            startIcon={<Edit />}
          >
            Edit with AI
          </Button>
        )}
        {editResult && (
          <>
            <Button onClick={handleCopyCode} startIcon={<ContentCopy />}>
              Copy Code
            </Button>
            {onApplyEdit && (
              <Button onClick={handleApply} variant="contained" color="primary">
                Apply Changes
              </Button>
            )}
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AIFileEditor;
