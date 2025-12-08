import React, { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { scansApi } from '../services/api';
import { Scan } from '../types';
import ScanHistory from '../components/Scans/ScanHistory';

const ScansPage: React.FC = () => {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadScans();
  }, []);

  const loadScans = async () => {
    try {
      const response = await scansApi.getAll();
      setScans(response.data);
    } catch (error) {
      console.error('Failed to load scans:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <h1>Scan History</h1>
      <ScanHistory scans={scans} />
    </Box>
  );
};

export default ScansPage;
