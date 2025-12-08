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
  Divider
} from '@mui/material';
import { PlayArrow, Timeline } from '@mui/icons-material';
import { projectsApi, scansApi } from '../../services/api';
import { Project, Scan } from '../../types';
import ScanHistory from '../Scans/ScanHistory';
import VulnerabilityStatusDialog from '../Vulnerabilities/VulnerabilityStatusDialog';

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [showVulnTracking, setShowVulnTracking] = useState(false);

  useEffect(() => {
    if (id) {
      loadProject(parseInt(id));
      loadScans(parseInt(id));
    }
  }, [id]);

  const loadProject = async (projectId: number) => {
    try {
      const response = await projectsApi.getById(projectId);
      setProject(response.data);
    } catch (error) {
      console.error('Failed to load project:', error);
    }
  };

  const loadScans = async (projectId: number) => {
    try {
      const response = await scansApi.getAll(projectId);
      setScans(response.data);
    } catch (error) {
      console.error('Failed to load scans:', error);
    }
  };

  const handleStartScan = async () => {
    if (!project) return;
    try {
      await scansApi.create({
        project_id: project.id,
        scan_type: 'full'
      });
      loadScans(project.id);
    } catch (error) {
      console.error('Failed to start scan:', error);
    }
  };

  if (!project) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h4">{project.name}</Typography>
            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                startIcon={<Timeline />}
                onClick={() => setShowVulnTracking(true)}
              >
                Vulnerability Tracking
              </Button>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleStartScan}
              >
                Start Scan
              </Button>
            </Box>
          </Box>

          <Chip label={project.framework} color="primary" sx={{ mb: 2 }} />

          <Typography variant="body1" color="textSecondary" paragraph>
            {project.description || 'No description'}
          </Typography>

          <Divider sx={{ my: 2 }} />

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="textSecondary">
                Repository
              </Typography>
              <Typography variant="body1">
                {project.repository_url || 'N/A'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="textSecondary">
                Total Scans
              </Typography>
              <Typography variant="body1">
                {project.total_scans || 0}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="textSecondary">
                Last Scan
              </Typography>
              <Typography variant="body1">
                {project.last_scan_date
                  ? new Date(project.last_scan_date).toLocaleDateString()
                  : 'Never'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Typography variant="h5" sx={{ mb: 2 }}>
        Scan History
      </Typography>
      <ScanHistory scans={scans} />

      {/* Vulnerability Tracking Dialog */}
      <VulnerabilityStatusDialog
        open={showVulnTracking}
        projectId={project.id}
        projectName={project.name}
        onClose={() => setShowVulnTracking(false)}
      />
    </Box>
  );
};

export default ProjectDetail;
