import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface GeneratePolicyRequest {
  policy_name: string;
  description: string;
  framework: 'terraform' | 'kubernetes' | 'dockerfile';
  example_code?: string;
}

export interface GeneratePolicyResponse {
  policy_code: string;
  policy_name: string;
  framework: string;
  description: string;
  example_usage: string;
}

export interface SuggestFixRequest {
  vulnerability_id: number;
}

export interface SuggestFixResponse {
  original_code: string;
  fixed_code: string;
  explanation: string;
  changes_summary: string[];
  risk_level: string;
}

export interface ApplyFixRequest {
  vulnerability_id: number;
  fixed_code?: string;
}

export interface ApplyFixResponse {
  success: boolean;
  file_path?: string;
  error?: string;
}

export interface EditFileRequest {
  file_content: string;
  file_path: string;
  user_instruction: string;
}

export interface EditFileResponse {
  original_code: string;
  edited_code: string;
  explanation: string;
  changes_made: string[];
}

export interface AnalyzeVulnerabilityRequest {
  check_id: string;
  check_name: string;
  resource_type?: string;
  description?: string;
}

export interface AnalyzeVulnerabilityResponse {
  severity_assessment: string;
  risk_explanation: string;
  potential_impact: string[];
  remediation_priority: string;
  recommended_actions: string[];
}

export interface AIStatusResponse {
  available: boolean;
  model: string;
}

class AIService {
  async checkStatus(): Promise<AIStatusResponse> {
    const response = await axios.get<AIStatusResponse>(`${API_BASE_URL}/ai/status`);
    return response.data;
  }

  async generatePolicy(request: GeneratePolicyRequest): Promise<GeneratePolicyResponse> {
    const response = await axios.post<GeneratePolicyResponse>(
      `${API_BASE_URL}/ai/generate-policy`,
      request
    );
    return response.data;
  }

  async suggestFix(request: SuggestFixRequest): Promise<SuggestFixResponse> {
    const response = await axios.post<SuggestFixResponse>(
      `${API_BASE_URL}/ai/suggest-fix`,
      request
    );
    return response.data;
  }

  async applyFix(request: ApplyFixRequest): Promise<ApplyFixResponse> {
    const response = await axios.post<ApplyFixResponse>(
      `${API_BASE_URL}/ai/apply-fix`,
      request
    );
    return response.data;
  }

  async editFile(request: EditFileRequest): Promise<EditFileResponse> {
    const response = await axios.post<EditFileResponse>(
      `${API_BASE_URL}/ai/edit-file`,
      request
    );
    return response.data;
  }

  async analyzeVulnerability(request: AnalyzeVulnerabilityRequest): Promise<AnalyzeVulnerabilityResponse> {
    const response = await axios.post<AnalyzeVulnerabilityResponse>(
      `${API_BASE_URL}/ai/analyze-vulnerability`,
      request
    );
    return response.data;
  }
}

export default new AIService();
