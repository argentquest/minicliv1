// Core application types
export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    model?: string;
    provider?: string;
    tokens?: number;
    codeBlocks?: CodeBlock[];
    mermaidDiagrams?: MermaidDiagram[];
  };
}

export interface CodeBlock {
  id: string;
  language: string;
  code: string;
  filename?: string;
}

export interface MermaidDiagram {
  id: string;
  code: string;
  title?: string;
}

export interface Tab {
  id: string;
  conversationId: string;
  title: string;
  isActive: boolean;
  isDirty: boolean;
}

export interface AppSettings {
  theme: 'light' | 'dark';
  provider: string;
  model: string;
  systemPrompt: string;
  contextFiles: string[];
  maxTokens: number;
  temperature: number;
}

export interface FileItem {
  path: string;
  name: string;
  size: number;
  isSelected: boolean;
  type: 'file' | 'directory';
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  contextFiles?: string[];
  settings?: Partial<AppSettings>;
}

export interface ChatResponse {
  message: Message;
  conversationId: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}