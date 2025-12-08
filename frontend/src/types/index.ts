// Type definitions
import { Framework } from '../constants/frameworks';

export interface Project {
  id: number;
  name: string;
  description?: string;
  repository_url?: string;
  framework: Framework;
  created_at: string;
  updated_at: string;
  total_scans?: number;
  last_scan_date?: string;
}

export interface Scan {
  id: number;
  project_id: number;
  scan_type: 'full' | 'incremental';
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  skipped_checks: number;
  scan_metadata?: any;
  error_message?: string;
}

export interface Vulnerability {
  id: number;
  scan_id: number;
  check_id: string;
  check_name: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  status: 'open' | 'in_progress' | 'resolved' | 'ignored';
  file_path: string;
  resource_type?: string;
  resource_name?: string;
  line_start?: number;
  line_end?: number;
  description?: string;
  remediation?: string;
  guideline_url?: string;
  detected_at: string;
  resolved_at?: string;
}

export interface DashboardStats {
  projects: {
    total_projects: number;
    active_projects: number;
    frameworks: Record<string, number>;
  };
  scans: {
    total_scans: number;
    completed_scans: number;
    failed_scans: number;
    average_pass_rate: number;
  };
  vulnerabilities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  trends: {
    scans: Array<{ date: string; value: number }>;
    vulnerabilities: Array<{ date: string; value: number }>;
    pass_rate: Array<{ date: string; value: number }>;
  };
  top_vulnerabilities: Array<{
    check_id: string;
    check_name: string;
    count: number;
    severity: string;
  }>;
  recent_scans: Array<{
    id: number;
    project_id: number;
    status: string;
    started_at: string;
    failed_checks: number;
  }>;
  vulnerabilities_by_project: Array<{
    project_name: string;
    failed_checks: number;
  }>;
}

export interface PolicyConfig {
  id: number;
  project_id?: number;
  policy_type: Framework;
  check_id: string;
  enabled: boolean;
  severity_override?: 'critical' | 'high' | 'medium' | 'low' | 'info';
  custom_message?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiError {
  detail: string;
}
