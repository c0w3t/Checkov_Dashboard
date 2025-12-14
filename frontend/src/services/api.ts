// API Service
import axios from 'axios';
import { Project, Scan, Vulnerability, DashboardStats } from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Enable cookies
});

// Handle 401 errors (session expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Session expired, redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Projects API
export const projectsApi = {
  getAll: () => api.get<Project[]>('/projects'),
  getById: (id: number) => api.get<Project>(`/projects/${id}`),
  create: (data: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => 
    api.post<Project>('/projects', data),
  update: (id: number, data: Partial<Project>) => 
    api.put<Project>(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
};

// Scans API
export const scansApi = {
  getAll: (projectId?: number) => 
    api.get<Scan[]>('/scans', { params: { project_id: projectId } }),
  getById: (id: number) => api.get<Scan>(`/scans/${id}`),
  create: (data: { project_id: number; scan_type: string; skip_checks?: string[] }) => 
    api.post<Scan>('/scans', data),
  update: (id: number, data: Partial<Scan>) => 
    api.put<Scan>(`/scans/${id}`, data),
  delete: (id: number) => api.delete(`/scans/${id}`),
};

// Vulnerabilities API
export const vulnerabilitiesApi = {
  getAll: (params?: { scan_id?: number; severity?: string; status_filter?: string }) => 
    api.get<Vulnerability[]>('/vulnerabilities', { params }),
  getById: (id: number) => api.get<Vulnerability>(`/vulnerabilities/${id}`),
  updateStatus: (id: number, status: string) => 
    api.patch<Vulnerability>(`/vulnerabilities/${id}/status`, null, { params: { new_status: status } }),
  getSummary: (projectId?: number) => 
    api.get('/vulnerabilities/statistics/summary', { params: { project_id: projectId } }),
};

// Dashboard API
export const dashboardApi = {
  getStats: () => api.get<DashboardStats>('/dashboard/stats'),
};

// Reports API
export const reportsApi = {
  generatePDF: (scanId: number) =>
    api.get(`/reports/${scanId}/pdf`, { responseType: 'blob' }),
  generateJSON: (scanId: number) =>
    api.get(`/reports/${scanId}/json`),
};

// Policies API
export const policiesApi = {
  getAll: (params?: { project_id?: number; policy_type?: string; enabled?: boolean }) =>
    api.get('/policies', { params }),
  getById: (id: number) => api.get(`/policies/${id}`),
  create: (data: any) => api.post('/policies', data),
  update: (id: number, data: any) => api.put(`/policies/${id}`, data),
  delete: (id: number) => api.delete(`/policies/${id}`),
  bulkToggle: (data: { check_ids: string[]; enabled: boolean; project_id?: number; policy_type?: string }) =>
    api.post('/policies/bulk-toggle', data),
};

// Notifications API
export const notificationsApi = {
  getSettings: (projectId: number) =>
    api.get(`/projects/${projectId}/notifications/settings`),
  updateSettings: (projectId: number, data: any) =>
    api.put(`/projects/${projectId}/notifications/settings`, data),
  sendTest: (projectId: number, notificationType: string) =>
    api.post(`/projects/${projectId}/notifications/test`, null, {
      params: { notification_type: notificationType }
    }),
  getHistory: (projectId: number, limit: number = 50) =>
    api.get(`/projects/${projectId}/notifications/history`, { params: { limit } }),
  getGlobalHistory: (limit: number = 100) =>
    api.get(`/notifications/history`, { params: { limit } }),
  clearHistory: (projectId: number) =>
    api.delete(`/projects/${projectId}/notifications/history`),
};

export default api;
