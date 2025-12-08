import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import { ContentCopy, AutoFixHigh, CheckCircle } from '@mui/icons-material';
import aiService, { SuggestFixRequest, SuggestFixResponse, ApplyFixRequest } from '../services/aiService';

interface AIFixSuggesterProps {
  open: boolean;
  onClose: () => void;
  vulnerability: {
    id: number;
    check_id: string;
    check_name: string;
    severity: string;
    description: string;
    resource_type?: string;
    file_path: string;
  };
}

const AIFixSuggester: React.FC<AIFixSuggesterProps> = ({
  open,
  onClose,
  vulnerability,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fixSuggestion, setFixSuggestion] = useState<SuggestFixResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);

  const handleGenerateFix = async () => {
    setLoading(true);
    setError(null);
    setFixSuggestion(null);

    const request: SuggestFixRequest = {
      vulnerability_id: vulnerability.id,
    };

    try {
      const result = await aiService.suggestFix(request);
      setFixSuggestion(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate fix suggestion. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (fixSuggestion) {
      navigator.clipboard.writeText(fixSuggestion.fixed_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    setFixSuggestion(null);
    setError(null);
    setApplyError(null);
    setApplySuccess(null);
    onClose();
  };
  const handleApplyFix = async () => {
    if (!fixSuggestion) return;
    setApplying(true);
    setApplyError(null);
    setApplySuccess(null);

    const request: ApplyFixRequest = {
      vulnerability_id: vulnerability.id,
      fixed_code: fixSuggestion.fixed_code,
    };

    try {
      const result = await aiService.applyFix(request);
      if (result.success) {
        setApplySuccess(`Applied fix to ${result.file_path}`);
      } else {
        setApplyError(result.error || 'Failed to apply fix.');
      }
    } catch (err: any) {
      setApplyError(err.response?.data?.detail || 'Failed to apply fix.');
    } finally {
      setApplying(false);
    }
  };

  React.useEffect(() => {
    if (open) {
      handleGenerateFix();
    }
  }, [open]);

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoFixHigh color="primary" />
        AI Fix Suggestion
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Vulnerability:
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {vulnerability.check_name}
            </Typography>
            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
              <Chip label={vulnerability.severity} color="error" size="small" />
              <Chip label={vulnerability.check_id} size="small" />
            </Box>
          </Box>

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Analyzing and generating fix...</Typography>
            </Box>
          )}

          {fixSuggestion && (
            <Box>
              <Alert severity="info" icon={<CheckCircle />} sx={{ mb: 2 }}>
                {fixSuggestion.risk_level && (
                  <Typography variant="body2" fontWeight="bold">
                    Risk Level: {fixSuggestion.risk_level}
                  </Typography>
                )}
                {fixSuggestion.explanation && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {fixSuggestion.explanation}
                  </Typography>
                )}
              </Alert>

              {applyError && (
                <Alert severity="error" sx={{ mb: 2 }}>{applyError}</Alert>
              )}
              {applySuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>{applySuccess}</Alert>
              )}

              {Array.isArray(fixSuggestion.changes_summary) && fixSuggestion.changes_summary.length > 0 && (
                <>
                  <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
                    Changes Summary:
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    {fixSuggestion.changes_summary.map((change, index) => (
                      <Chip key={index} label={change} size="small" sx={{ mr: 1, mb: 1 }} />
                    ))}
                  </Box>
                </>
              )}

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  Original Code:
                </Typography>
              </Box>
              <Paper sx={{ p: 2, bgcolor: '#ffebee', maxHeight: 200, overflow: 'auto', mb: 2 }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                  {fixSuggestion.original_code}
                </pre>
              </Paper>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  Fixed Code:
                </Typography>
                <Tooltip title={copied ? 'Copied!' : 'Copy fixed code'}>
                  <IconButton onClick={handleCopyCode} size="small">
                    <ContentCopy />
                  </IconButton>
                </Tooltip>
              </Box>
              <Paper sx={{ p: 2, bgcolor: '#e8f5e9', maxHeight: 200, overflow: 'auto' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                  {fixSuggestion.fixed_code}
                </pre>
              </Paper>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        {fixSuggestion && (
          <Button
            onClick={handleCopyCode}
            variant="contained"
            startIcon={<ContentCopy />}
          >
            Copy Fixed Code
          </Button>
        )}
        {fixSuggestion && (
          <Button
            onClick={handleApplyFix}
            variant="contained"
            color="secondary"
            startIcon={<AutoFixHigh />}
            disabled={applying}
          >
            {applying ? 'Applying...' : 'Apply Fix'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AIFixSuggester;
