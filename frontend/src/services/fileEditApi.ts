// API for file editing and scan in one step
import axios from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api';

export const fileEditApi = {
  // Get file content for editing
  getFileContent: async (uploadId: string, filePath: string) => {
    const response = await axios.get(`${API_BASE_URL}/scans/upload/${uploadId}/file`, {
      params: { file_path: filePath },
    });
    return response.data;
  },
  // Update file content and scan in one step
  updateAndScan: async (uploadId: string, filePath: string, content: string) => {
    const response = await axios.post(`${API_BASE_URL}/scans/upload/${uploadId}/file/scan`, {
      file_path: filePath,
      content,
    });
    return response.data;
  },
};
