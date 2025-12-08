import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import { ContentCopy, AutoAwesome, Save } from '@mui/icons-material';
import axios from 'axios';
import { SUPPORTED_FRAMEWORKS } from '../constants/frameworks';
import aiService, { GeneratePolicyRequest, GeneratePolicyResponse } from '../services/aiService';

interface AIPolicyGeneratorProps {
  open: boolean;
  onClose: () => void;
  onPolicyGenerated?: (policy: GeneratePolicyResponse) => void;
}

const AIPolicyGenerator: React.FC<AIPolicyGeneratorProps> = ({ open, onClose, onPolicyGenerated }) => {
  const [formData, setFormData] = useState<GeneratePolicyRequest>({
    policy_name: '',
    description: '',
    framework: 'terraform',
    example_code: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedPolicy, setGeneratedPolicy] = useState<GeneratePolicyResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [severity, setSeverity] = useState<'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'>('MEDIUM');

  const handleInputChange = (field: keyof GeneratePolicyRequest, value: string) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleGenerate = async () => {
    if (!formData.policy_name || !formData.description) {
      setError('Please provide policy name and description');
      return;
    }

    setLoading(true);
    setError(null);
    setGeneratedPolicy(null);

    try {
      const result = await aiService.generatePolicy(formData);
      setGeneratedPolicy(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate policy. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (generatedPolicy) {
      navigator.clipboard.writeText(generatedPolicy.policy_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    setFormData({
      policy_name: '',
      description: '',
      framework: 'terraform',
      example_code: '',
    });
    setGeneratedPolicy(null);
    setError(null);
    setSeverity('MEDIUM');
    onClose();
  };

  const handleSave = async () => {
    if (!generatedPolicy?.policy_code) {
      setError('No generated policy to save');
      return;
    }

    const payload = {
      platform: formData.framework,
      check_id: formData.policy_name,
      name: formData.description || formData.policy_name,
      severity,
      format: 'python',
      code: generatedPolicy.policy_code,
    };

    try {
      await axios.post('http://localhost:8000/api/policies/custom/create', payload);
      if (onPolicyGenerated) onPolicyGenerated(generatedPolicy);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save custom policy');
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoAwesome color="primary" />
        AI Policy Generator
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <TextField
            label="Policy Name"
            value={formData.policy_name}
            onChange={(e) => handleInputChange('policy_name', e.target.value)}
            fullWidth
            required
            placeholder="e.g., CKV_AWS_123"
          />

          <TextField
            label="Framework"
            value={formData.framework}
            onChange={(e) => handleInputChange('framework', e.target.value)}
            select
            fullWidth
            required
          >
            {SUPPORTED_FRAMEWORKS.map(fw => (
              <MenuItem key={fw.value} value={fw.value}>{fw.label}</MenuItem>
            ))}
          </TextField>

          <TextField
            label="Severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value as any)}
            select
            fullWidth
            required
          >
            <MenuItem value="CRITICAL">Critical</MenuItem>
            <MenuItem value="HIGH">High</MenuItem>
            <MenuItem value="MEDIUM">Medium</MenuItem>
            <MenuItem value="LOW">Low</MenuItem>
            <MenuItem value="INFO">Info</MenuItem>
          </TextField>

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            fullWidth
            required
            multiline
            rows={3}
            placeholder="Describe what security check this policy should perform..."
          />

          <TextField
            label="Example Code (Optional)"
            value={formData.example_code}
            onChange={(e) => handleInputChange('example_code', e.target.value)}
            fullWidth
            multiline
            rows={4}
            placeholder="Provide example code that should fail this check (optional)..."
          />

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
              <CircularProgress />
            </Box>
          )}

          {generatedPolicy && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6">Generated Policy:</Typography>
                <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
                  <IconButton onClick={handleCopyCode} size="small">
                    <ContentCopy />
                  </IconButton>
                </Tooltip>
              </Box>
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5', maxHeight: 400, overflow: 'auto' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                  {generatedPolicy.policy_code}
                </pre>
              </Paper>
              <Typography variant="body2" sx={{ mt: 2, fontWeight: 'bold' }}>
                Example Usage:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5', mt: 1 }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                  {generatedPolicy.example_usage}
                </pre>
              </Paper>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        <Button
          onClick={handleSave}
          variant="outlined"
          disabled={loading || !generatedPolicy}
          startIcon={<Save />}
        >
          Save as Custom Policy
        </Button>
        <Button
          onClick={handleGenerate}
          variant="contained"
          disabled={loading}
          startIcon={<AutoAwesome />}
        >
          Generate Policy
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AIPolicyGenerator;
