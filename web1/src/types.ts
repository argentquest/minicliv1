export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  rawContent?: string;
  timestamp: string;
  tokensUsed?: number;
  processingTime?: number;
  modelUsed?: string;
  contextFiles?: string[];
}

export interface QuickCommand {
  key: string;
  value: string;
}

export interface SystemMessageOption {
  id: string;
  label: string;
  description?: string;
}

export interface SystemMessageRecord {
  filename: string;
  display_name: string;
  preview: string;
  length: number;
  is_current: boolean;
}

export interface QuestionStatus {
  question: string;
  status: string;
  response: string;
  timestamp: string;
  tokensUsed: number;
  processingTime: number;
  modelUsed: string;
}

export interface ConversationHistoryEntry {
  role: ChatRole;
  content: string;
}

export interface ConversationSummary {
  conversationId: string;
  provider: string;
  selectedModel: string;
  selectedDirectory: string;
  selectedFiles: string[];
  persistentFiles: string[];
  questionHistory: QuestionStatus[];
  conversationHistory: ConversationHistoryEntry[];
}

export interface ConversationCreateResponse {
  conversationId: string;
  provider: string;
  model: string;
  availableModels: string[];
  summary: ConversationSummary;
}

export interface AskQuestionResponse {
  response: string;
  processingTime: number;
  tokensUsed: number;
  questionIndex: number;
  summary: ConversationSummary;
}

export interface SystemPromptResponse {
  response: string;
  processingTime: number;
  tokensUsed: number;
  summary: ConversationSummary;
}

export interface QuickCommandResponseEntry {
  key: string;
  value: string;
}

export interface UiDefaultsResponse {
  provider: string;
  models: string[];
  defaultModel: string;
  toolCommands: QuickCommandResponseEntry[];
  systemMessages: {
    current: string;
    messages: SystemMessageRecord[];
  };
  apiKey?: string;
}

export interface HeaderActionHandlers {
  onSetContext: () => void;
  onSendQuestion: () => void;
  onExecuteSystem: () => void;
  onClearResponse: () => void;
  onNewConversation: () => void;
  onSaveHistory: () => void;
  onLoadHistory: () => void;
  onOpenSettings: () => void;
  onToggleTheme: () => void;
  onOpenSystemMessage: () => void;
  onOpenAbout: () => void;
}

export type HeaderAction = keyof HeaderActionHandlers;

export type ThemeName = 'light' | 'dark';

export interface CodebaseFile {
  path: string;
  relativePath: string;
  size: number;
  modifiedTime: number;
  extension: string;
  isSpecial: boolean;
}

export interface SetDirectoryResponse {
  directory: string;
  files: CodebaseFile[];
  message: string;
  summary: ConversationSummary;
}

export interface UpdateFilesResponse extends ConversationSummary {}

export interface ExportConversationResponse {
  summary: ConversationSummary;
}


export interface TopFoldersResponse {
  folders: string[];
}
