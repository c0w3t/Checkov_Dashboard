import React, { useState, useEffect } from 'react';
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
  FormControlLabel,
  Switch,
  Box,
} from '@mui/material';
import { PolicyConfig } from '../../types';
import { SUPPORTED_FRAMEWORKS, Framework } from '../../constants/frameworks';

interface PolicyConfigDialogProps {
  open: boolean;
  policy?: PolicyConfig | null;
  onClose: () => void;
  onSave: (data: any) => void;
}

const PolicyConfigDialog: React.FC<PolicyConfigDialogProps> = ({
  open,
  policy,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState({
    policy_type: 'terraform' as Framework,
    check_id: '',
    enabled: true,
    severity_override: '',
    custom_message: '',
    project_id: '',
  });

  useEffect(() => {
    if (policy) {
      setFormData({
        policy_type: policy.policy_type,
        check_id: policy.check_id,
        enabled: policy.enabled,
        severity_override: policy.severity_override || '',
        custom_message: policy.custom_message || '',
        project_id: policy.project_id?.toString() || '',
      });
    } else {
      setFormData({
        policy_type: 'terraform',
        check_id: '',
        enabled: true,
        severity_override: '',
        custom_message: '',
        project_id: '',
      });
    }
  }, [policy]);

  const handleSubmit = () => {
    const submitData: any = {
      policy_type: formData.policy_type,
      check_id: formData.check_id,
      enabled: formData.enabled,
    };

    if (formData.severity_override) {
      submitData.severity_override = formData.severity_override;
    }

    if (formData.custom_message) {
      submitData.custom_message = formData.custom_message;
    }

    if (formData.project_id) {
      submitData.project_id = parseInt(formData.project_id);
    }

    onSave(submitData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {policy ? 'Edit Policy Configuration' : 'Add Policy Configuration'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <FormControl fullWidth>
            <InputLabel>Policy Type</InputLabel>
            <Select
              value={formData.policy_type}
              label="Policy Type"
              onChange={(e) =>
                setFormData({
                  ...formData,
                  policy_type: e.target.value as Framework,
                })
              }
              disabled={!!policy}
            >
              {SUPPORTED_FRAMEWORKS.map(fw => (
                <MenuItem key={fw.value} value={fw.value}>{fw.label}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Check ID"
            value={formData.check_id}
            onChange={(e) =>
              setFormData({ ...formData, check_id: e.target.value })
            }
            disabled={!!policy}
            required
            placeholder="e.g., CKV_TF_CUSTOM_10"
          />

          <TextField
            fullWidth
            label="Project ID (Optional)"
            value={formData.project_id}
            onChange={(e) =>
              setFormData({ ...formData, project_id: e.target.value })
            }
            type="number"
            helperText="Leave empty to apply globally"
          />

          <FormControl fullWidth>
            <InputLabel>Severity Override</InputLabel>
            <Select
              value={formData.severity_override}
              label="Severity Override"
              onChange={(e) =>
                setFormData({ ...formData, severity_override: e.target.value })
              }
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="info">Info</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Custom Message"
            value={formData.custom_message}
            onChange={(e) =>
              setFormData({ ...formData, custom_message: e.target.value })
            }
            multiline
            rows={3}
          />

          <FormControlLabel
            control={
              <Switch
                checked={formData.enabled}
                onChange={(e) =>
                  setFormData({ ...formData, enabled: e.target.checked })
                }
              />
            }
            label="Enabled"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!formData.check_id}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PolicyConfigDialog;
