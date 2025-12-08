import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Box
} from '@mui/material';
import { formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';

interface RecentScansProps {
  scans: Array<{
    id: number;
    project_id: number;
    project_name?: string;
    status: string;
    started_at: string;
    failed_checks: number;
    severity?: {
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
    };
  }>;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'running':
      return 'info';
    default:
      return 'default';
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return '#d32f2f';
    case 'high':
      return '#f57c00';
    case 'medium':
      return '#fbc02d';
    case 'low':
      return '#388e3c';
    case 'info':
      return '#1976d2';
    default:
      return '#718096';
  }
};


const RecentScans: React.FC<RecentScansProps> = ({ scans }) => {
  const navigate = useNavigate();

  return (
    <Card sx={{ 
      height: '100%',
      background: '#ffffff',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      borderRadius: 2,
      border: '1px solid #e2e8f0',
      transition: 'all 0.2s ease',
      '&:hover': {
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      }
    }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ mb: 2.5 }}>
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 700,
              fontSize: '1.125rem',
              color: '#1a202c',
              mb: 0.5,
              letterSpacing: '-0.3px'
            }}
          >
            Recent Scans
          </Typography>
          <Typography variant="body2" sx={{ color: '#718096', fontSize: '0.875rem' }}>
            Latest security scan results
          </Typography>
        </Box>
        {scans.length === 0 ? (
          <Box
            sx={{
              py: 4,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 2,
              }}
            >
              <Typography variant="h3" sx={{ color: '#667eea', fontSize: '2.5rem' }}>🔍</Typography>
            </Box>
            <Typography variant="body1" sx={{ fontWeight: 600, color: '#2d3748' }}>
              No scans yet
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
              Start scanning your projects
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {scans.map((scan, index) => (
              <ListItem 
                key={scan.id}
                sx={{ 
                  px: 2.5,
                  py: 2.5,
                  mb: index < scans.length - 1 ? 1.5 : 0,
                  cursor: 'pointer',
                  borderRadius: 2,
                  background: '#f7fafc',
                  border: '1px solid #e2e8f0',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    background: '#edf2f7',
                    borderColor: '#667eea',
                  },
                }}
                onClick={() => navigate(`/scans/${scan.id}`)}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1, flexWrap: 'wrap' }}>
                      <Typography variant="body1" sx={{ fontWeight: 700, color: '#2d3748', fontSize: '0.95rem' }}>
                        Scan #{scan.id}
                      </Typography>
                      {scan.project_name && (
                        <Typography variant="body2" sx={{ color: '#718096', fontWeight: 500, fontSize: '0.875rem' }}>
                          • {scan.project_name}
                        </Typography>
                      )}
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                      <Typography variant="body2" sx={{ color: '#a0aec0', display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '0.85rem' }}>
                        <span>⏱</span>
                        {formatDistanceToNow(new Date(scan.started_at + 'Z'), { addSuffix: true })}
                      </Typography>
                      {scan.failed_checks > 0 ? (
                        <>
                          <Box
                            sx={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              px: 1.5,
                              py: 0.5,
                              borderRadius: 1.5,
                              backgroundColor: '#ef4444',
                              border: 'none',
                            }}
                          >
                            <Typography
                              variant="body2"
                              sx={{ 
                                color: '#ffffff',
                                fontWeight: 700,
                                fontSize: '0.75rem',
                              }}
                            >
                              {scan.failed_checks} issues
                            </Typography>
                          </Box>
                          {scan.severity && (
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {scan.severity.critical > 0 && (
                                <Chip
                                  label="Critical"
                                  size="small"
                                  sx={{
                                    backgroundColor: getSeverityColor('critical'),
                                    color: '#ffffff',
                                    fontWeight: 600,
                                    fontSize: '0.7rem',
                                    height: '22px',
                                  }}
                                />
                              )}
                              {scan.severity.high > 0 && (
                                <Chip
                                  label="High"
                                  size="small"
                                  sx={{
                                    backgroundColor: getSeverityColor('high'),
                                    color: '#ffffff',
                                    fontWeight: 600,
                                    fontSize: '0.7rem',
                                    height: '22px',
                                  }}
                                />
                              )}
                              {scan.severity.medium > 0 && (
                                <Chip
                                  label="Medium"
                                  size="small"
                                  sx={{
                                    backgroundColor: getSeverityColor('medium'),
                                    color: '#ffffff',
                                    fontWeight: 600,
                                    fontSize: '0.7rem',
                                    height: '22px',
                                  }}
                                />
                              )}
                              {scan.severity.low > 0 && (
                                <Chip
                                  label="Low"
                                  size="small"
                                  sx={{
                                    backgroundColor: getSeverityColor('low'),
                                    color: '#ffffff',
                                    fontWeight: 600,
                                    fontSize: '0.7rem',
                                    height: '22px',
                                  }}
                                />
                              )}
                              {scan.severity.info > 0 && (
                                <Chip
                                  label="Info"
                                  size="small"
                                  sx={{
                                    backgroundColor: getSeverityColor('info'),
                                    color: '#ffffff',
                                    fontWeight: 600,
                                    fontSize: '0.7rem',
                                    height: '22px',
                                  }}
                                />
                              )}
                            </Box>
                          )}
                        </>
                      ) : (
                        <Chip
                          label="No Issues"
                          size="small"
                          sx={{
                            backgroundColor: '#48bb78',
                            color: '#ffffff',
                            fontWeight: 600,
                            fontSize: '0.7rem',
                            height: '22px',
                          }}
                        />
                      )}
                    </Box>
                  }
                />
                <Chip
                  label={scan.status}
                  size="small"
                  color={getStatusColor(scan.status) as any}
                  sx={{ 
                    fontWeight: 700,
                    fontSize: '0.75rem',
                    height: '28px',
                    minWidth: '85px',
                  }}
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentScans;
