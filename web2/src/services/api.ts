import axios from 'axios';
import type { ApiResponse, ChatRequest, ChatResponse, Conversation, AppSettings, FileItem } from '../types';

const API_BASE_URL = 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    if (error.response?.status === 401) {
      // Handle authentication errors
      console.warn('Authentication required');
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error:', error.response.status);
    }
    return Promise.reject(error);
  }
);

export class ApiService {
  // Chat endpoints
  static async sendMessage(request: ChatRequest): Promise<ApiResponse<ChatResponse>> {
    try {
      const response = await api.post('/chat', request);
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to send message',
      };
    }
  }

  // Conversation endpoints
  static async getConversations(): Promise<ApiResponse<Conversation[]>> {
    try {
      const response = await api.get('/conversations');
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch conversations',
      };
    }
  }

  static async getConversation(id: string): Promise<ApiResponse<Conversation>> {
    try {
      const response = await api.get(`/conversations/${id}`);
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch conversation',
      };
    }
  }

  static async saveConversation(conversation: Conversation): Promise<ApiResponse<Conversation>> {
    try {
      const response = await api.post('/conversations', conversation);
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to save conversation',
      };
    }
  }

  static async deleteConversation(id: string): Promise<ApiResponse<void>> {
    try {
      const response = await api.delete(`/conversations/${id}`);
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to delete conversation',
      };
    }
  }

  // File context endpoints
  static async getFiles(directory?: string): Promise<ApiResponse<FileItem[]>> {
    try {
      const params = directory ? { directory } : {};
      const response = await api.get('/files', { params });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch files',
      };
    }
  }

  static async loadDirectory(path: string): Promise<ApiResponse<FileItem[]>> {
    try {
      const response = await api.post('/files/load', { path });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to load directory',
      };
    }
  }

  // Settings endpoints
  static async getSettings(): Promise<ApiResponse<AppSettings>> {
    try {
      const response = await api.get('/settings');
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch settings',
      };
    }
  }

  static async updateSettings(settings: Partial<AppSettings>): Promise<ApiResponse<AppSettings>> {
    try {
      const response = await api.put('/settings', settings);
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to update settings',
      };
    }
  }

  // System endpoints
  static async getSystemInfo(): Promise<ApiResponse<any>> {
    try {
      const response = await api.get('/system/info');
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch system info',
      };
    }
  }

  static async executeSystemPrompt(prompt: string): Promise<ApiResponse<ChatResponse>> {
    try {
      const response = await api.post('/system/execute', { prompt });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to execute system prompt',
      };
    }
  }

  // NEW: Code extraction endpoint
  static async extractCode(messageId: string): Promise<ApiResponse<CodeBlock[]>> {
    try {
      const response = await api.post('/code/extract', { messageId });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to extract code',
      };
    }
  }

  // NEW: Mermaid diagram rendering endpoint
  static async renderMermaid(code: string, title?: string): Promise<ApiResponse<string>> {
    try {
      const response = await api.post('/mermaid/render', { code, title });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to render mermaid diagram',
      };
    }
  }
}

export default ApiService;