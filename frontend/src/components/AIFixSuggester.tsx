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
  Select,
  MenuItem,
} from '@mui/material';
import { ContentCopy, AutoFixHigh, CheckCircle, PlayCircleOutline } from '@mui/icons-material';
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
  const [provider, setProvider] = useState<'openai' | 'gemini'>('openai');
  const [copied, setCopied] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);
  const [scanSuccess, setScanSuccess] = useState<string | null>(null);
  const [editedCode, setEditedCode] = useState<string>('');

  const computeDiffLines = (original: string, fixed: string) => {
    const o = original.split('\n');
    const f = fixed.split('\n');
    const len = Math.max(o.length, f.length);
    const rows: { type: 'same' | 'change'; left?: string; right?: string }[] = [];
    for (let i = 0; i < len; i++) {
      const ol = o[i] ?? '';
      const fl = f[i] ?? '';
      rows.push({ type: ol === fl ? 'same' : 'change', left: ol, right: fl });
    }
    return rows;
  };

  const handleGenerateFix = async () => {
    setLoading(true);
    setError(null);
    setFixSuggestion(null);

    const request: SuggestFixRequest = {
      vulnerability_id: vulnerability.id,
      provider,
    };

    try {
      const result = await aiService.suggestFix(request);
      setFixSuggestion(result);
      if (result?.fixed_code) {
        setEditedCode(result.fixed_code);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate fix suggestion. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    const toCopy = editedCode || fixSuggestion?.fixed_code || '';
    if (toCopy) {
      navigator.clipboard.writeText(toCopy);
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
      fixed_code: editedCode || fixSuggestion.fixed_code,
      provider,
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

  const handleTriggerScan = async () => {
    setScanSuccess(null);
    setApplyError(null);
    try {
      const res = await aiService.triggerScan({ vulnerability_id: vulnerability.id });
      if (res.success) {
        setScanSuccess(`Triggered scan #${res.scan_id}`);
      } else {
        setApplyError(res.error || 'Failed to trigger scan.');
      }
    } catch (err: any) {
      setApplyError(err.response?.data?.detail || 'Failed to trigger scan.');
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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="subtitle2">Provider:</Typography>
            <Select size="small" value={provider} onChange={(e) => setProvider(e.target.value as 'openai' | 'gemini')}>
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="gemini">Gemini</MenuItem>
            </Select>
          </Box>
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
              {scanSuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>{scanSuccess}</Alert>
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
                <textarea
                  value={editedCode}
                  onChange={(e) => setEditedCode(e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: 160,
                    border: 'none',
                    outline: 'none',
                    background: 'transparent',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                  }}
                />
              </Paper>

              {fixSuggestion?.original_code && (editedCode || fixSuggestion?.fixed_code) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
                    Diff Preview:
                  </Typography>
                  <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto', bgcolor: '#f5f5f5' }}>
                    <pre style={{ margin: 0 }}>
                      {computeDiffLines(fixSuggestion.original_code, editedCode || fixSuggestion.fixed_code).map((row, idx) => (
                        <div key={idx} style={{ background: row.type === 'change' ? '#fff3e0' : 'transparent' }}>
                          <span style={{ color: '#b71c1c' }}>{row.left}</span>
                          <span>{'  =>  '}</span>
                          <span style={{ color: '#1b5e20' }}>{row.right}</span>
                        </div>
                      ))}
                    </pre>
                  </Paper>
                </Box>
              )}
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
        {fixSuggestion && (
          <Button
            onClick={handleTriggerScan}
            variant="outlined"
            color="primary"
            startIcon={<PlayCircleOutline />}
          >
            Trigger Scan
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AIFixSuggester;
