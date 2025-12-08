import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer 
} from 'recharts';

interface TrendChartProps {
  data: Array<{
    date: string;
    scans: number;
    vulnerabilities: number;
    passRate: number;
  }>;
}

const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  // Filter out days with no data and format date for display
  const filteredData = data
    .filter(item => item.scans > 0 || item.vulnerabilities > 0)
    .map(item => ({
      ...item,
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }));

  // If only one data point, add padding points for better visualization
  const displayData = filteredData.length === 1 
    ? [
        { ...filteredData[0], scans: 0, vulnerabilities: 0, passRate: 0 },
        filteredData[0],
        { ...filteredData[0], scans: 0, vulnerabilities: 0, passRate: 0 },
      ]
    : filteredData;

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
        <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem', color: '#2d3748', mb: 0.5 }}>
          Security Trends (Last 30 Days)
        </Typography>
        <Typography variant="body2" sx={{ color: '#718096', fontSize: '0.875rem', mb: 3 }}>
          Track security metrics over time
        </Typography>
        {filteredData.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ p: 4, textAlign: 'center' }}>
            No trend data available. Run some scans to see trends.
          </Typography>
        ) : (
          <>
            {filteredData.length === 1 && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Showing today's scan results. Run more scans over time to see trends.
              </Typography>
            )}
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={displayData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12, fill: '#718096' }}
                  stroke="#cbd5e0"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12, fill: '#718096' }} stroke="#cbd5e0" />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="scans" 
                  stroke="#667eea" 
                  name="Scans"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#667eea' }}
                  activeDot={{ r: 6 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="vulnerabilities" 
                  stroke="#f56565" 
                  name="Vulnerabilities"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#f56565' }}
                  activeDot={{ r: 6 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="passRate" 
                  stroke="#48bb78" 
                  name="Pass Rate %"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#48bb78' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        )}
      </CardContent>
    </Card>
  );
};;

export default TrendChart;
