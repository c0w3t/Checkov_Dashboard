import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: number;
  color?: string;
  gradient?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ 
  title, 
  value, 
  icon, 
  trend, 
  color = '#1976d2',
  gradient
}) => {
  
  return (
    <Card 
      sx={{ 
        height: '100%',
        background: '#ffffff',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        borderRadius: 2,
        border: '1px solid #e2e8f0',
        transition: 'all 0.2s ease',
        '&:hover': {
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }
      }}
    >
      <CardContent sx={{ position: 'relative', zIndex: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography 
              sx={{ 
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                color: '#a0aec0',
                mb: 1,
                letterSpacing: '0.8px'
              }}
            >
              {title}
            </Typography>
            <Typography 
              variant="h3" 
              component="div" 
              sx={{ 
                fontWeight: 800,
                color: '#1a202c',
                mb: 1,
                fontSize: '2rem',
                letterSpacing: '-1px'
              }}
            >
              {value}
            </Typography>
            {trend !== undefined && (
              <Box display="flex" alignItems="center">
                {trend >= 0 ? (
                  <TrendingUp fontSize="small" sx={{ mr: 0.5 }} />
                ) : (
                  <TrendingDown fontSize="small" sx={{ mr: 0.5 }} />
                )}
                <Typography 
                  variant="body2"
                  sx={{ opacity: 0.9 }}
                >
                  {trend >= 0 ? '+' : ''}{trend}% from last month
                </Typography>
              </Box>
            )}
          </Box>
          <Box 
            sx={{ 
              background: gradient || `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
              borderRadius: '12px',
              p: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: `0 4px 12px ${color}40`,
              '& > svg': {
                fontSize: '2rem'
              }
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatsCard;
