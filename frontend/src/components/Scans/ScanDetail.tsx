import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Divider,
  CircularProgress
} from '@mui/material';
import { GetApp, Edit } from '@mui/icons-material';
import { scansApi, vulnerabilitiesApi, reportsApi } from '../../services/api';
import { Scan, Vulnerability } from '../../types';
import VulnerabilityList from '../Vulnerabilities/VulnerabilityList';
import FileEditorDialog from './FileEditorDialog';
import axios from 'axios';
import { fileEditApi } from '../../services/fileEditApi';

const ScanDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorFileName, setEditorFileName] = useState('');
  const [editorFileContent, setEditorFileContent] = useState('');
  const [editorUploadId, setEditorUploadId] = useState<string | null>(null);
  const [editorLoading, setEditorLoading] = useState(false);

  useEffect(() => {
    if (id) {
      loadScanDetail(parseInt(id));
    }
  }, [id]);

  const loadScanDetail = async (scanId: number) => {
    try {
      const [scanResponse, vulnResponse] = await Promise.all([
        scansApi.getById(scanId),
        vulnerabilitiesApi.getAll({ scan_id: scanId })
      ]);
      setScan(scanResponse.data);
      setVulnerabilities(vulnResponse.data);
    } catch (error) {
      console.error('Failed to load scan details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!scan) return;
    try {
      const response = await reportsApi.generatePDF(scan.id);
      
      // Handle download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scan_${scan.id}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to generate PDF report. Please try again.');
    }
  };

  const openEditFromScan = async () => {
    if (!scan) return;
    // Derive upload_id from scan metadata if available
    const uploadPath = (scan.scan_metadata as any)?.upload_path;
    if (!uploadPath) {
      alert('No upload context available for this scan.');
      return;
    }
    // upload_id format is "<projectId>_<timestamp>"; find from path .../uploads/project_<id>/<timestamp>
    try {
      const parts = uploadPath.split('/');
      const idx = parts.lastIndexOf(`project_${scan.project_id}`);
      const timestamp = parts[idx + 1];
      const uploadId = `${scan.project_id}_${timestamp}`;
      setEditorUploadId(uploadId);
      setEditorLoading(true);
      // Fetch files in upload
      const filesResp = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${uploadId}/files`
      );
      const files = filesResp.data.files;
      if (!files || files.length === 0) {
        alert('No files found in this upload.');
        setEditorLoading(false);
        return;
      }
      const filePath = files[0].path;
      setEditorFileName(files[0].name || filePath.split('/').pop() || filePath);
      // Fetch file content using the same API as Project Detail
      const contentResp = await fileEditApi.getFileContent(uploadId, filePath);
      setEditorFileContent(contentResp.content || contentResp.data?.content || '');
      setEditorOpen(true);
    } catch (e) {
      console.error(e);
      alert('Failed to load file for editing');
    } finally {
      setEditorLoading(false);
    }
  };

  const handleSaveAndScan = async (content: string) => {
    if (!editorUploadId || !editorFileName) return { success: false, error: 'No file selected' };
    try {
      // Re-fetch file list to get full relative path
      const filesResp = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${editorUploadId}/files`
      );
      const files = filesResp.data.files;
      if (!files || files.length === 0) return { success: false, error: 'No files found' };
      const filePath = files[0].path;
      const result = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/scans/upload/${editorUploadId}/file/scan`,
        { file_path: filePath, content }
      );
      // Reload details after scan
      await loadScanDetail(scan.id);
      return { success: true, result: result.data };
    } catch (err: any) {
      return { success: false, error: err.response?.data?.detail || 'Failed to update and scan' };
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!scan) {
    return <Typography>Scan not found</Typography>;
  }

  const passRate = scan.total_checks > 0 
    ? ((scan.passed_checks / scan.total_checks) * 100).toFixed(1)
    : 0;

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h4">Scan #{scan.id}</Typography>
            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                startIcon={<Edit />}
                onClick={openEditFromScan}
                disabled={editorLoading}
              >
                Edit & Scan
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<GetApp />}
                onClick={handleDownloadReport}
              >
                Download PDF Report
              </Button>
            </Box>
          </Box>

          <Chip 
            label={scan.status} 
            color={scan.status === 'completed' ? 'success' : 'warning'}
            sx={{ mb: 2 }}
          />

          <Divider sx={{ my: 2 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Started At
              </Typography>
              <Typography variant="body1">
                {new Date(scan.started_at).toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Completed At
              </Typography>
              <Typography variant="body1">
                {scan.completed_at 
                  ? new Date(scan.completed_at).toLocaleString()
                  : 'In progress...'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Pass Rate
              </Typography>
              <Typography variant="h5" color={parseFloat(passRate as string) >= 80 ? 'success.main' : 'warning.main'}>
                {passRate}%
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Total Checks
              </Typography>
              <Typography variant="h5">
                {scan.total_checks}
              </Typography>
            </Grid>
          </Grid>

          <Box mt={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box textAlign="center" p={2} bgcolor="success.light" borderRadius={1}>
                  <Typography variant="h4" color="success.dark">
                    {scan.passed_checks}
                  </Typography>
                  <Typography variant="subtitle2">Passed</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box textAlign="center" p={2} bgcolor="error.light" borderRadius={1}>
                  <Typography variant="h4" color="error.dark">
                    {scan.failed_checks}
                  </Typography>
                  <Typography variant="subtitle2">Failed</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box textAlign="center" p={2} bgcolor="grey.300" borderRadius={1}>
                  <Typography variant="h4">
                    {scan.skipped_checks}
                  </Typography>
                  <Typography variant="subtitle2">Skipped</Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>

          {scan.error_message && (
            <Box mt={2} p={2} bgcolor="error.light" borderRadius={1}>
              <Typography variant="subtitle2" color="error.dark">
                Error: {scan.error_message}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      <Typography variant="h5" sx={{ mb: 2 }}>
        Vulnerabilities
      </Typography>
      <VulnerabilityList vulnerabilities={vulnerabilities} />
      <FileEditorDialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        fileName={editorFileName}
        initialContent={editorFileContent}
        onSaveAndScan={handleSaveAndScan}
      />
    </Box>
  );
};

export default ScanDetail;
