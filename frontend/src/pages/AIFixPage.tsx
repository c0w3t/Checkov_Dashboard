import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Container, Typography, Select, MenuItem, Paper, CircularProgress, Alert, IconButton, Tooltip, Button, Divider } from '@mui/material';
import { ContentCopy, AutoFixHigh, PlayCircleOutline } from '@mui/icons-material';
import aiService, { SuggestFixRequest, SuggestFixResponse, ApplyFixRequest } from '../services/aiService';

const AIFixPage: React.FC = () => {
  const { id } = useParams();
  const vulnId = Number(id);
  const [provider, setProvider] = React.useState<'openai' | 'gemini'>('openai');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [fixSuggestion, setFixSuggestion] = React.useState<SuggestFixResponse | null>(null);
  const [editedCode, setEditedCode] = React.useState('');
  const [copied, setCopied] = React.useState(false);
  const [applying, setApplying] = React.useState(false);
  const [applyError, setApplyError] = React.useState<string | null>(null);
  const [applySuccess, setApplySuccess] = React.useState<string | null>(null);
  const [scanSuccess, setScanSuccess] = React.useState<string | null>(null);
  const [showOnlyChanges, setShowOnlyChanges] = React.useState(true);

  const sanitizeContent = (s: string) => {
    if (!s) return '';
    let t = s.trim();
    // Strip surrounding quotes from whole-file string artifacts
    if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
      t = t.slice(1, -1);
    }
    // Normalize line endings and trailing spaces
    t = t.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    // Remove trailing spaces per line
    t = t.split('\n').map((line) => line.replace(/\s+$/g, '')).join('\n');
    return t;
  };

  const computeDiffLines = (original: string, fixed: string) => {
    const o = original.split('\n');
    const f = fixed.split('\n');
    const len = Math.max(o.length, f.length);
    return Array.from({ length: len }).map((_, i) => ({ left: o[i] ?? '', right: f[i] ?? '' }));
  };

  const renderTokenDiff = (left: string, right: string) => {
    // Show only the fixed (right) line, with changed tokens highlighted.
    const lTokens = left.split(/(\s+)/);
    const rTokens = right.split(/(\s+)/);
    const max = Math.max(lTokens.length, rTokens.length);
    const rParts: React.ReactNode[] = [];
    const norm = (t: string) => t.replace(/\s+/g, ' ').trim();
    for (let i = 0; i < max; i++) {
      const lt = lTokens[i] ?? '';
      const rt = rTokens[i] ?? '';
      const isSpace = /\s+/.test(rt);
      const changed = norm(lt) !== norm(rt) && !isSpace;
      rParts.push(
        <span
          key={`r-${i}`}
          style={{
            backgroundColor: changed ? '#e8f5e9' : 'transparent',
            color: changed ? '#1b5e20' : '#555',
          }}
        >
          {rt}
        </span>
      );
    }
    return <div>{rParts}</div>;
  };

  const loadFix = async () => {
    if (!vulnId) return;
    setLoading(true);
    setError(null);
    setFixSuggestion(null);
    try {
      const req: SuggestFixRequest = { vulnerability_id: vulnId, provider };
      const res = await aiService.suggestFix(req);
      setFixSuggestion(res);
      if (res?.fixed_code) setEditedCode(sanitizeContent(res.fixed_code));
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to generate fix suggestion.');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadFix();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vulnId, provider]);

  const handleCopy = () => {
    const toCopy = editedCode || fixSuggestion?.fixed_code || '';
    if (toCopy) {
      navigator.clipboard.writeText(toCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleApply = async () => {
    if (!vulnId || !fixSuggestion) return;
    setApplying(true);
    setApplyError(null);
    setApplySuccess(null);
    try {
      const req: ApplyFixRequest = { vulnerability_id: vulnId, fixed_code: editedCode || fixSuggestion.fixed_code, provider };
      const res = await aiService.applyFix(req);
      if (res.success) setApplySuccess(`Applied fix to ${res.file_path}`);
      else setApplyError(res.error || 'Failed to apply fix');
    } catch (e: any) {
      setApplyError(e.response?.data?.detail || 'Failed to apply fix');
    } finally {
      setApplying(false);
    }
  };

  const handleTriggerScan = async () => {
    setScanSuccess(null);
    setApplyError(null);
    try {
      const res = await aiService.triggerScan({ vulnerability_id: vulnId, fixed_code: editedCode || fixSuggestion?.fixed_code });
      if (res.success) setScanSuccess(`Triggered scan #${res.scan_id}`);
      else setApplyError(res.error || 'Failed to trigger scan');
    } catch (e: any) {
      setApplyError(e.response?.data?.detail || 'Failed to trigger scan');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center" gap={2}>
          <AutoFixHigh color="primary" />
          <Typography variant="h5" fontWeight={700}>AI Fix Suggestion</Typography>
          <Typography variant="subtitle2" color="text.secondary">Provider:</Typography>
          <Select size="small" value={provider} onChange={(e) => setProvider(e.target.value as 'openai' | 'gemini')}>
            <MenuItem value="openai">OpenAI</MenuItem>
            <MenuItem value="gemini">Gemini</MenuItem>
          </Select>
        </Box>
        <Box display="flex" gap={1}>
          <Tooltip title={copied ? 'Copied!' : 'Copy fixed code'}>
            <IconButton onClick={handleCopy} size="small">
              <ContentCopy />
            </IconButton>
          </Tooltip>
          <Button variant="contained" color="secondary" onClick={handleApply} disabled={applying}>
            {applying ? 'Applying...' : 'Apply Fix'}
          </Button>
          <Button variant="outlined" color="primary" onClick={handleTriggerScan} startIcon={<PlayCircleOutline />}>Trigger Scan</Button>
        </Box>
      </Box>
      <Divider sx={{ mb: 2 }} />

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {applyError && <Alert severity="error" sx={{ mb: 2 }}>{applyError}</Alert>}
      {scanSuccess && <Alert severity="success" sx={{ mb: 2 }}>{scanSuccess}</Alert>}
      {applySuccess && <Alert severity="success" sx={{ mb: 2 }}>{applySuccess}</Alert>}

      {loading ? (
        <Box display="flex" justifyContent="center" my={4}><CircularProgress /></Box>
      ) : (
        fixSuggestion && (
          <Box
            display="grid"
            gridTemplateColumns={{ xs: '1fr', md: '1fr 1fr 1fr' }}
            gap={2}
            sx={{
              alignItems: 'stretch',
            }}
          >
            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: { xs: 'auto', md: '70vh' } }}>
              <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1 }}>Original Code</Typography>
              <Box component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'monospace', fontSize: '0.95rem', bgcolor: '#ffebee', p: 2, borderRadius: 1, overflow: 'auto', flexGrow: 1 }}>
                {fixSuggestion.original_code}
              </Box>
            </Paper>

            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: { xs: 'auto', md: '70vh' } }}>
              <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1 }}>Fixed Code</Typography>
              <Box sx={{ bgcolor: '#e8f5e9', p: 2, borderRadius: 1, flexGrow: 1 }}>
                <textarea
                  value={editedCode}
                  onChange={(e) => setEditedCode(e.target.value)}
                  style={{ width: '100%', height: '100%', minHeight: 0, border: 'none', outline: 'none', background: 'transparent', fontFamily: 'monospace', fontSize: '0.95rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflow: 'auto' }}
                />
              </Box>
            </Paper>

            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: { xs: 'auto', md: '70vh' } }}>
              <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1 }}>Diff Preview</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography variant="caption" color="text.secondary">View:</Typography>
                <Button size="small" variant={showOnlyChanges ? 'contained' : 'outlined'} onClick={() => setShowOnlyChanges(true)}>Only changes</Button>
                <Button size="small" variant={!showOnlyChanges ? 'contained' : 'outlined'} onClick={() => setShowOnlyChanges(false)}>All lines</Button>
              </Box>
              <Box component="pre" sx={{ m: 0, fontFamily: 'monospace', fontSize: '0.95rem', bgcolor: '#f5f5f5', p: 2, borderRadius: 1, overflow: 'auto', flexGrow: 1, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {computeDiffLines(sanitizeContent(fixSuggestion.original_code), editedCode || sanitizeContent(fixSuggestion.fixed_code))
                  .filter((row) => !showOnlyChanges || row.left !== row.right)
                  .map((row, idx) => (
                    <div key={idx}>{renderTokenDiff(row.left, row.right)}</div>
                  ))}
              </Box>
            </Paper>
          </Box>
        )
      )}
    </Container>
  );
};

export default AIFixPage;