import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box, Toolbar } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ProjectsPage from './pages/ProjectsPage';
import ScansPage from './pages/ScansPage';
import ReportsPage from './pages/ReportsPage';
import PoliciesPage from './pages/PoliciesPage';
import SettingsPage from './pages/SettingsPage';
import ProjectDetail from './components/Projects/ProjectDetail';
import ScanDetail from './components/Scans/ScanDetail';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#667eea',
    },
    secondary: {
      main: '#764ba2',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#2d3748',
      secondary: '#718096',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 10px rgba(0,0,0,0.08)',
          borderRadius: 12,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
        },
      },
    },
  },
});

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                    {/* Permanent Sidebar */}
                    {sidebarOpen && (
                      <Box
                        sx={{
                          width: 240,
                          flexShrink: 0,
                          backgroundColor: '#2d3436',
                          borderRight: '1px solid #e2e8f0',
                        }}
                      >
                        <Sidebar />
                      </Box>
                    )}
                    {/* Main Content Area */}
                    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box
                        component="main"
                        sx={{
                          flexGrow: 1,
                          p: 3,
                          backgroundColor: '#f5f7fa',
                        }}
                      >
                        <Header onMenuClick={handleSidebarToggle} />
                        <Toolbar />
                        <Routes>
                          <Route path="/" element={<DashboardPage />} />
                          <Route path="/projects" element={<ProjectsPage />} />
                          <Route path="/projects/:id" element={<ProjectDetail />} />
                          <Route path="/scans" element={<ScansPage />} />
                          <Route path="/scans/:id" element={<ScanDetail />} />
                          <Route path="/reports" element={<ReportsPage />} />
                          <Route path="/policies" element={<PoliciesPage />} />
                          <Route path="/settings" element={<SettingsPage />} />
                        </Routes>
                      </Box>
                    </Box>
                  </Box>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
