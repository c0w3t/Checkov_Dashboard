import React, { useState, useMemo, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Tabs,
  Tab,
  Typography,
  Alert,
} from '@mui/material';
import { Code as CodeIcon } from '@mui/icons-material';
import { SUPPORTED_FRAMEWORKS, FRAMEWORK_CATEGORIES } from '../../constants/frameworks';

interface CreatePolicyDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}

// Move template generation outside component for better performance
const getTemplate = (platform: string, format: number, checkId: string, name: string) => {
  if (format === 1) {
    // YAML template
    return `metadata:
  id: ${checkId || 'CKV_XX_CUSTOM_XX'}
  name: ${name || 'Custom Check Name'}
  category: ENCRYPTION
  
definition:
  cond_type: attribute
  resource_types:
    - aws_s3_bucket
  attribute: encryption
  operator: exists
`;
  }

  // Python templates
  if (platform === 'kubernetes') {
    return `"""
Custom Kubernetes Policy: ${name || 'Policy Name'}
ID: ${checkId || 'CKV_K8S_CUSTOM_XX'}
"""

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class CustomK8sCheck(BaseK8Check):
    def __init__(self) -> None:
        name = "${name || 'Custom Kubernetes Check'}"
        id = "${checkId || 'CKV_K8S_CUSTOM_XX'}"
        supported_kind = ("Pod", "Deployment", "StatefulSet")
        categories = (CheckCategories.GENERAL,)
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def scan_spec_conf(self, conf):
        """
        Implement your Kubernetes check logic here
        """
        spec = conf.get("spec", {})
        
        # Example: Check for security context
        if spec.get("securityContext"):
            return CheckResult.PASSED
        
        return CheckResult.FAILED


check = CustomK8sCheck()
`;
  }

  if (platform === 'dockerfile') {
    return `"""
Custom Dockerfile Policy: ${name || 'Policy Name'}
ID: ${checkId || 'CKV_DOCKER_CUSTOM_XX'}
"""

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.checks.base_dockerfile_check import BaseDockerfileCheck


class CustomDockerCheck(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "${name || 'Custom Dockerfile Check'}"
        id = "${checkId || 'CKV_DOCKER_CUSTOM_XX'}"
        categories = (CheckCategories.CONVENTION,)
        super().__init__(name=name, id=id, categories=categories)

    def scan_resource_conf(self, conf):
        """
        Implement your Dockerfile check logic here
        """
        # Example: Check for USER instruction
        for instruction in conf:
            if instruction.get("instruction") == "USER":
                return CheckResult.PASSED
        
        return CheckResult.FAILED


check = CustomDockerCheck()
`;
  }

  // Default Terraform template
  return `"""
Custom Policy: ${name || 'Policy Name'}
ID: ${checkId || 'CKV_XX_CUSTOM_XX'}
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class CustomCheck(BaseResourceCheck):
    def __init__(self) -> None:
        name = "${name || 'Custom Check Name'}"
        id = "${checkId || 'CKV_XX_CUSTOM_XX'}"
        supported_resources = ("aws_s3_bucket",)  # Add your resources here
        categories = (CheckCategories.ENCRYPTION,)  # Adjust category
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Implement your check logic here
        """
        # Example: Check if a specific attribute exists
        if conf.get("encryption"):
            return CheckResult.PASSED
        
        return CheckResult.FAILED


check = CustomCheck()
`;
};

const CreatePolicyDialog: React.FC<CreatePolicyDialogProps> = ({
  open,
  onClose,
  onSave,
}) => {
  const [platform, setPlatform] = useState('terraform');
  const [checkId, setCheckId] = useState('');
  const [name, setName] = useState('');
  const [severity, setSeverity] = useState('MEDIUM');
  const [format, setFormat] = useState(0); // 0 = Python, 1 = YAML
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [codeInitialized, setCodeInitialized] = useState(false);

  // Memoize template generation
  const currentTemplate = useMemo(() => {
    return getTemplate(platform, format, checkId, name);
  }, [platform, format, checkId, name]);

  // Initialize code only when dialog opens or when user changes platform/format
  React.useEffect(() => {
    if (open && !codeInitialized) {
      setCode(currentTemplate);
      setCodeInitialized(true);
    }
  }, [open, currentTemplate, codeInitialized]);

  // Reset form when dialog closes
  React.useEffect(() => {
    if (!open) {
      // Reset state when dialog closes
      setPlatform('terraform');
      setCheckId('');
      setName('');
      setSeverity('MEDIUM');
      setFormat(0);
      setCode('');
      setError('');
      setCodeInitialized(false);
    }
  }, [open]);

  // Update code when format or platform changes (but only if already initialized)
  React.useEffect(() => {
    if (codeInitialized) {
      setCode(currentTemplate);
    }
  }, [format, platform, codeInitialized, currentTemplate]);

  // Use useCallback to avoid recreating functions on every render
  const handleSave = useCallback(async () => {
    setError('');

    // Validation
    if (!checkId) {
      setError('Check ID is required');
      return;
    }
    if (!name) {
      setError('Name is required');
      return;
    }
    if (!code) {
      setError('Code is required');
      return;
    }

    setSaving(true);
    try {
      await onSave({
        platform,
        check_id: checkId,
        name,
        severity,
        format: format === 0 ? 'python' : 'yaml',
        code,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create policy');
    } finally {
      setSaving(false);
    }
  }, [checkId, name, code, platform, severity, format, onSave, onClose]);

  const generateCheckId = useCallback(() => {
    const prefix = platform === 'kubernetes' ? 'CKV_K8S' : platform === 'dockerfile' ? 'CKV_DOCKER' : 'CKV_TF';
    const timestamp = Date.now().toString().slice(-4);
    setCheckId(`${prefix}_CUSTOM_${timestamp}`);
  }, [platform]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CodeIcon />
          <Typography variant="h6">Create Custom Policy</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          <FormControl fullWidth>
            <InputLabel>Platform</InputLabel>
            <Select
              value={platform}
              label="Platform"
              onChange={(e) => setPlatform(e.target.value)}
            >
              {Object.entries(FRAMEWORK_CATEGORIES).map(([category, frameworks]) => [
                <MenuItem key={category} disabled sx={{ fontWeight: 'bold', fontSize: '0.85em', color: 'text.secondary' }}>
                  {category}
                </MenuItem>,
                ...frameworks.map(fw => {
                  const item = SUPPORTED_FRAMEWORKS.find(f => f.value === fw);
                  return item ? (
                    <MenuItem key={item.value} value={item.value} sx={{ pl: 4 }}>
                      {item.label}
                    </MenuItem>
                  ) : null;
                })
              ])}
            </Select>
          </FormControl>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              label="Check ID"
              value={checkId}
              onChange={(e) => setCheckId(e.target.value.toUpperCase())}
              placeholder="CKV_TF_CUSTOM_XX"
              required
              helperText="Unique identifier for this policy"
            />
            <Button
              variant="outlined"
              onClick={generateCheckId}
              sx={{ minWidth: 120 }}
            >
              Generate ID
            </Button>
          </Box>

          <TextField
            fullWidth
            label="Policy Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Ensure S3 bucket has encryption enabled"
            required
          />

          <FormControl fullWidth>
            <InputLabel>Severity</InputLabel>
            <Select
              value={severity}
              label="Severity"
              onChange={(e) => setSeverity(e.target.value)}
            >
              <MenuItem value="CRITICAL">Critical</MenuItem>
              <MenuItem value="HIGH">High</MenuItem>
              <MenuItem value="MEDIUM">Medium</MenuItem>
              <MenuItem value="LOW">Low</MenuItem>
              <MenuItem value="INFO">Info</MenuItem>
            </Select>
          </FormControl>

          <Box>
            <Tabs value={format} onChange={(_, v) => setFormat(v)}>
              <Tab label="Python" />
              <Tab label="YAML" />
            </Tabs>
          </Box>

          <TextField
            fullWidth
            multiline
            rows={18}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter your policy code here..."
            sx={{
              '& textarea': {
                fontFamily: 'monospace',
                fontSize: '0.875rem',
              },
            }}
          />

          <Typography variant="caption" color="text.secondary">
            {format === 0
              ? 'Write Python code using Checkov\'s BaseResourceCheck class'
              : 'Write YAML policy using Checkov\'s YAML format'}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={saving}>
          {saving ? 'Creating...' : 'Create Policy'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreatePolicyDialog;
