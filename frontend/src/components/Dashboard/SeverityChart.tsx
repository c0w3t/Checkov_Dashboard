import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface SeverityChartProps {
  data: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}

const COLORS = {
  critical: '#d32f2f',
  high: '#f57c00',
  medium: '#fbc02d',
  low: '#388e3c',
  info: '#1976d2',
};

const SeverityChart: React.FC<SeverityChartProps> = ({ data }) => {
  const chartData = [
    { name: 'Critical', value: data.critical, color: COLORS.critical },
    { name: 'High', value: data.high, color: COLORS.high },
    { name: 'Medium', value: data.medium, color: COLORS.medium },
    { name: 'Low', value: data.low, color: COLORS.low },
    { name: 'Info', value: data.info, color: COLORS.info },
  ].filter(item => item.value > 0);

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
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ mb: 2 }}>
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
            Vulnerabilities by Severity
          </Typography>
          <Typography variant="body2" sx={{ color: '#718096', fontSize: '0.875rem' }}>
            Distribution of security issues
          </Typography>
        </Box>
        {chartData.length === 0 ? (
          <Box
            sx={{
              height: 300,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'text.secondary',
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 2,
              }}
            >
              <Typography variant="h3" sx={{ fontSize: '2.5rem' }}>✓</Typography>
            </Box>
            <Typography variant="body1" sx={{ fontWeight: 600, color: '#2d3748' }}>No vulnerabilities found</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>All checks passed successfully</Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={85}
                innerRadius={55}
                fill="#8884d8"
                dataKey="value"
                paddingAngle={2}
                strokeWidth={0}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0];
                    return (
                      <Box
                        sx={{
                          backgroundColor: '#ffffff',
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                          p: 1.5,
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#2d3748', mb: 0.5 }}>
                          {data.name}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#718096', fontSize: '0.85rem' }}>
                          {data.value} vulnerabilities
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Legend 
                wrapperStyle={{
                  paddingTop: '10px',
                  fontSize: '13px'
                }}
                iconType="circle"
                iconSize={8}
                formatter={(value, entry: any) => (
                  <span style={{ color: '#4a5568', fontSize: '13px', fontWeight: 500 }}>
                    {value}: {entry.payload.value}
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default SeverityChart;
