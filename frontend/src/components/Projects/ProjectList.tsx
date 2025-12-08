import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  LinearProgress,
  Collapse,
} from '@mui/material';
import { 
  Add, 
  Edit, 
  Delete, 
  Visibility, 
  PlayArrow, 
  History,
  BugReport,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  CloudUpload,
  ExpandMore,
  ExpandLess
} from '@mui/icons-material';
import { projectsApi, scansApi } from '../../services/api';
import { Project } from '../../types';
import { useNavigate } from 'react-router-dom';
import FileUploadDialog from './FileUploadDialog';
import UploadListDialog from './UploadListDialog';
import { SUPPORTED_FRAMEWORKS, Framework } from '../../constants/frameworks';

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [open, setOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadListDialogOpen, setUploadListDialogOpen] = useState(false);
  const [scanDialogOpen, setScanDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [scanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [scanError, setScanError] = useState('');
  const [expandedVulns, setExpandedVulns] = useState<Set<number>>(new Set());
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    repository_url: '',
    framework: 'terraform' as Framework
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectsApi.getAll();
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleOpen = (project?: Project) => {
    if (project) {
      setEditingProject(project);
      setFormData({
        name: project.name,
        description: project.description || '',
        repository_url: project.repository_url || '',
        framework: project.framework
      });
    } else {
      setEditingProject(null);
      setFormData({
        name: '',
        description: '',
        repository_url: '',
        framework: 'terraform'
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingProject(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingProject) {
        await projectsApi.update(editingProject.id, formData);
      } else {
        await projectsApi.create(formData);
      }
      handleClose();
      loadProjects();
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await projectsApi.delete(id);
        loadProjects();
      } catch (error) {
        console.error('Failed to delete project:', error);
      }
    }
  };

  const handleViewProject = (project: Project) => {
    navigate(`/projects/${project.id}`);
  };

  const handleOpenUpload = (project: Project) => {
    setSelectedProject(project);
    setUploadDialogOpen(true);
  };

  const handleCloseUpload = () => {
    setUploadDialogOpen(false);
    setSelectedProject(null);
    // Reload to show new uploads
    loadProjects();
  };

  const handleUploadComplete = (uploadId: string, totalFiles: number) => {
    // Show success message and reload
    console.log(`Uploaded ${totalFiles} files with ID: ${uploadId}`);
    loadProjects();
    setUploadDialogOpen(false);
    // Open upload list dialog to show available uploads
    setUploadListDialogOpen(true);
  };

  const handleOpenUploadList = (project: Project) => {
    setSelectedProject(project);
    setUploadListDialogOpen(true);
  };

  const handleCloseUploadList = () => {
    setUploadListDialogOpen(false);
    setSelectedProject(null);
  };

  const handleScanStart = async (scanId: number) => {
    // Open scan result dialog
    handleOpenScanResult(scanId);
  };

  const handleOpenScanResult = async (scanId: number) => {
    try {
      const response = await scansApi.getById(scanId);
      setScanResult(response.data);
      setScanDialogOpen(true);
    } catch (error) {
      console.error('Failed to load scan result:', error);
    }
  };

  const handleCloseScanDialog = () => {
    setScanDialogOpen(false);
    setSelectedProject(null);
    setScanResult(null);
    setScanError('');
  };

  const getFrameworkColor = (framework: string) => {
    switch (framework) {
      case 'terraform':
        return 'primary';
      case 'kubernetes':
        return 'secondary';
      case 'dockerfile':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={2}>
        <h2>Projects</h2>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpen()}
        >
          New Project
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Framework</TableCell>
              <TableCell>Repository</TableCell>
              <TableCell>Total Scans</TableCell>
              <TableCell>Last Scan</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.map((project) => (
              <TableRow key={project.id}>
                <TableCell>
                  <Typography variant="subtitle2">{project.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {project.description}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={project.framework}
                    color={getFrameworkColor(project.framework) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap style={{ maxWidth: 200 }}>
                    {project.repository_url || 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>{project.total_scans || 0}</TableCell>
                <TableCell>
                  {project.last_scan_date 
                    ? new Date(project.last_scan_date).toLocaleDateString()
                    : 'Never'}
                </TableCell>
                <TableCell>
                  <IconButton 
                    size="small" 
                    color="secondary"
                    onClick={() => handleOpenUpload(project)}
                    title="Upload Files"
                  >
                    <CloudUpload />
                  </IconButton>
                  <IconButton 
                    size="small" 
                    color="primary"
                    onClick={() => handleOpenUploadList(project)}
                    title="Scan Uploaded Files"
                  >
                    <PlayArrow />
                  </IconButton>
                  <IconButton 
                    size="small" 
                    onClick={() => handleViewProject(project)}
                    title="View Details"
                  >
                    <Visibility />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleOpen(project)}>
                    <Edit />
                  </IconButton>
                  <IconButton 
                    size="small" 
                    color="error"
                    onClick={() => handleDelete(project.id)}
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingProject ? 'Edit Project' : 'New Project'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Project Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
          <TextField
            fullWidth
            label="Repository URL"
            value={formData.repository_url}
            onChange={(e) => setFormData({ ...formData, repository_url: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            select
            label="Framework"
            value={formData.framework}
            onChange={(e) => setFormData({ ...formData, framework: e.target.value as Framework })}
            margin="normal"
          >
            {SUPPORTED_FRAMEWORKS.map(fw => (
              <MenuItem key={fw.value} value={fw.value}>{fw.label}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingProject ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Scan Result Dialog */}
      <Dialog 
        open={scanDialogOpen} 
        onClose={handleCloseScanDialog} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <BugReport />
            <span>Scan Results - {selectedProject?.name}</span>
          </Box>
        </DialogTitle>
        <DialogContent>
          {scanning && (
            <Box textAlign="center" py={4}>
              <CircularProgress />
              <Typography variant="body1" mt={2}>
                Scanning in progress...
              </Typography>
              <LinearProgress sx={{ mt: 2 }} />
            </Box>
          )}

          {scanError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="subtitle2">Scan Failed</Typography>
              <Typography variant="body2">{scanError}</Typography>
            </Alert>
          )}

          {scanResult && !scanning && (
            <Box>
              <Alert 
                severity={scanResult.failed_checks === 0 ? 'success' : 'warning'} 
                sx={{ mb: 2 }}
              >
                <Typography variant="subtitle2">
                  Scan Completed
                </Typography>
                <Typography variant="body2">
                  Status: {scanResult.status}
                </Typography>
              </Alert>

              <Box display="flex" gap={2} mb={3}>
                <Paper sx={{ flex: 1, p: 2, bgcolor: 'success.light' }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <CheckCircle color="success" />
                    <div>
                      <Typography variant="h4">
                        {scanResult.passed_checks || 0}
                      </Typography>
                      <Typography variant="caption">Passed</Typography>
                    </div>
                  </Box>
                </Paper>

                <Paper sx={{ flex: 1, p: 2, bgcolor: 'error.light' }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <ErrorIcon color="error" />
                    <div>
                      <Typography variant="h4">
                        {scanResult.failed_checks || 0}
                      </Typography>
                      <Typography variant="caption">Failed</Typography>
                    </div>
                  </Box>
                </Paper>

                <Paper sx={{ flex: 1, p: 2, bgcolor: 'warning.light' }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Warning color="warning" />
                    <div>
                      <Typography variant="h4">
                        {scanResult.skipped_checks || 0}
                      </Typography>
                      <Typography variant="caption">Skipped</Typography>
                    </div>
                  </Box>
                </Paper>
              </Box>

              {scanResult.vulnerabilities && scanResult.vulnerabilities.length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Vulnerabilities Found ({scanResult.vulnerabilities.length})
                  </Typography>
                  <List dense>
                    {scanResult.vulnerabilities.slice(0, 10).map((vuln: any, index: number) => (
                      <Box key={index}>
                        <ListItem 
                          button
                          onClick={() => {
                            const newExpanded = new Set(expandedVulns);
                            if (newExpanded.has(index)) {
                              newExpanded.delete(index);
                            } else {
                              newExpanded.add(index);
                            }
                            setExpandedVulns(newExpanded);
                          }}
                        >
                          <ListItemIcon>
                            {expandedVulns.has(index) ? <ExpandLess /> : <ExpandMore />}
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box display="flex" alignItems="center" gap={1}>
                                <Chip 
                                  label={vuln.severity} 
                                  size="small"
                                  color={
                                    vuln.severity === 'CRITICAL' ? 'error' :
                                    vuln.severity === 'HIGH' ? 'warning' :
                                    vuln.severity === 'MEDIUM' ? 'info' : 'default'
                                  }
                                />
                                <Typography variant="body2">
                                  {vuln.check_id}: {vuln.check_name}
                                </Typography>
                              </Box>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                {vuln.file_path} (Line {vuln.line_number || 'N/A'})
                              </Typography>
                            }
                          />
                        </ListItem>
                        <Collapse in={expandedVulns.has(index)} timeout="auto" unmountOnExit>
                          <Box sx={{ pl: 4, pr: 2, pb: 2 }}>
                            {vuln.description && (
                              <Box mb={2}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Description:
                                </Typography>
                                <Box 
                                  component="pre" 
                                  sx={{ 
                                    p: 2, 
                                    bgcolor: 'grey.100', 
                                    borderRadius: 1,
                                    overflow: 'auto',
                                    fontSize: '0.75rem',
                                    whiteSpace: 'pre-wrap',
                                    fontFamily: 'monospace',
                                    maxHeight: 300
                                  }}
                                >
                                  {vuln.description}
                                </Box>
                              </Box>
                            )}
                            {vuln.remediation && (
                              <Box mb={2}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Remediation:
                                </Typography>
                                <Box 
                                  component="pre" 
                                  sx={{ 
                                    p: 2, 
                                    bgcolor: 'grey.100', 
                                    borderRadius: 1,
                                    overflow: 'auto',
                                    fontSize: '0.75rem',
                                    whiteSpace: 'pre-wrap',
                                    fontFamily: 'monospace'
                                  }}
                                >
                                  {vuln.remediation}
                                </Box>
                              </Box>
                            )}
                            {vuln.guideline_url && (
                              <Typography variant="caption">
                                <a href={vuln.guideline_url} target="_blank" rel="noopener noreferrer">
                                  View Guideline →
                                </a>
                              </Typography>
                            )}
                          </Box>
                        </Collapse>
                      </Box>
                    ))}
                  </List>
                  {scanResult.vulnerabilities.length > 10 && (
                    <Typography variant="caption" color="text.secondary">
                      ... and {scanResult.vulnerabilities.length - 10} more
                    </Typography>
                  )}
                </>
              )}

              {(!scanResult.vulnerabilities || scanResult.vulnerabilities.length === 0) && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    No vulnerabilities found! Your infrastructure is secure.
                  </Typography>
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseScanDialog}>Close</Button>
          {scanResult && (
            <Button 
              variant="contained" 
              startIcon={<History />}
              onClick={() => navigate(`/projects/${scanResult.project_id}`)}
            >
              View Full Report
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* File Upload Dialog */}
      {selectedProject && (
        <>
          <FileUploadDialog
            open={uploadDialogOpen}
            projectId={selectedProject.id}
            projectName={selectedProject.name}
            onClose={handleCloseUpload}
            onUploadComplete={handleUploadComplete}
          />
          <UploadListDialog
            open={uploadListDialogOpen}
            projectId={selectedProject.id}
            projectName={selectedProject.name}
            onClose={handleCloseUploadList}
            onScanStart={handleScanStart}
          />
        </>
      )}
    </Box>
  );
};

export default ProjectList;
