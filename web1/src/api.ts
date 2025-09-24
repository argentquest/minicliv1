
import { appConfig } from './config';
import type {
  AskQuestionResponse,
  ConversationCreateResponse,
  ConversationSummary,
  ExportConversationResponse,
  SetDirectoryResponse,
  SettingsResponse,
  SystemPromptResponse,
  UiDefaultsResponse,
} from './types';

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = Array.isArray(data.detail)
          ? data.detail.map((item: any) => item.msg ?? item).join(', ')
          : String(data.detail);
      }
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options;
  const headers = new Headers();
  const init: RequestInit = { method, headers, signal };

  if (body !== undefined) {
    headers.set('Content-Type', 'application/json');
    init.body = JSON.stringify(body);
  }

  const response = await fetch(`${appConfig.backendBaseUrl}${path}`, init);
  return handleResponse<T>(response);
}

export async function fetchUiDefaults(signal?: AbortSignal): Promise<UiDefaultsResponse> {
  return request<UiDefaultsResponse>('/meta/ui-defaults', { signal });
}

export interface CreateConversationRequest {
  provider?: string;
  model?: string;
  apiKey?: string;
}

export async function createConversation(
  payload: CreateConversationRequest,
  signal?: AbortSignal,
): Promise<ConversationCreateResponse> {
  return request<ConversationCreateResponse>('/conversations', {
    method: 'POST',
    body: {
      provider: payload.provider,
      model: payload.model,
      apiKey: payload.apiKey,
    },
    signal,
  });
}

export interface AskQuestionPayload {
  question: string;
  selectedFiles?: string[];
  persistent?: boolean;
}

export async function askQuestion(
  conversationId: string,
  payload: AskQuestionPayload,
  signal?: AbortSignal,
): Promise<AskQuestionResponse> {
  return request<AskQuestionResponse>(`/conversations/${conversationId}/question`, {
    method: 'POST',
    body: {
      question: payload.question,
      selectedFiles: payload.selectedFiles,
      persistent: payload.persistent ?? false,
    },
    signal,
  });
}

export async function runSystemPrompt(conversationId: string, signal?: AbortSignal): Promise<SystemPromptResponse> {
  return request<SystemPromptResponse>(`/conversations/${conversationId}/system-prompt`, {
    method: 'POST',
    signal,
  });
}

export async function setConversationModel(
  conversationId: string,
  model: string,
  signal?: AbortSignal,
): Promise<ConversationCreateResponse> {
  return request<ConversationCreateResponse>(`/conversations/${conversationId}/model`, {
    method: 'PUT',
    body: { model },
    signal,
  });
}

export async function setConversationApiKey(
  conversationId: string,
  apiKey: string,
  signal?: AbortSignal,
): Promise<ConversationCreateResponse> {
  return request<ConversationCreateResponse>(`/conversations/${conversationId}/api-key`, {
    method: 'PUT',
    body: { apiKey },
    signal,
  });
}

export async function setDirectory(
  conversationId: string,
  path: string,
  signal?: AbortSignal,
): Promise<SetDirectoryResponse> {
  return request<SetDirectoryResponse>(`/conversations/${conversationId}/directory`, {
    method: 'POST',
    body: { path },
    signal,
  });
}

export async function updateSelectedFiles(
  conversationId: string,
  files: string[],
  persistent: boolean,
  signal?: AbortSignal,
): Promise<ConversationSummary> {
  return request<ConversationSummary>(`/conversations/${conversationId}/files`, {
    method: 'POST',
    body: {
      selectedFiles: files,
      persistent,
    },
    signal,
  });
}

export async function clearConversation(
  conversationId: string,
  signal?: AbortSignal,
): Promise<ConversationSummary> {
  return request<ConversationSummary>(`/conversations/${conversationId}/clear`, {
    method: 'POST',
    signal,
  });
}

export async function deleteConversation(conversationId: string, signal?: AbortSignal): Promise<void> {
  await request(`/conversations/${conversationId}`, {
    method: 'DELETE',
    signal,
  });
}

export async function exportConversation(
  conversationId: string,
  signal?: AbortSignal,
): Promise<ExportConversationResponse> {
  return request<ExportConversationResponse>(`/conversations/${conversationId}/export`, {
    method: 'GET',
    signal,
  });
}

export async function importConversation(
  payload: unknown,
  signal?: AbortSignal,
): Promise<ConversationCreateResponse> {
  return request<ConversationCreateResponse>('/conversations/import', {
    method: 'POST',
    body: payload,
    signal,
  });
}

export async function toggleTheme(signal?: AbortSignal): Promise<{ theme: string; message: string }> {
  return request<{ theme: string; message: string }>('/settings/theme/toggle', {
    method: 'POST',
    signal,
  });
}

export async function setSystemMessage(filename: string, signal?: AbortSignal): Promise<{ current: string }> {
  return request<{ current: string }>('/system-messages/current', {
    method: 'PUT',
    body: { filename },
    signal,
  });
}

export async function fetchSystemMessageContent(
  filename: string,
  signal?: AbortSignal,
): Promise<{ filename: string; content: string; htmlContent: string }> {
  return request<{ filename: string; content: string; htmlContent: string }>(`/system-messages/${encodeURIComponent(filename)}`, {
    method: 'GET',
    signal,
  });
}

export async function saveSystemMessage(
  filename: string,
  content: string,
  signal?: AbortSignal,
): Promise<{ filename: string }> {
  return request<{ filename: string }>('/system-messages', {
    method: 'POST',
    body: { filename, content },
    signal,
  });
}

export async function deleteSystemMessage(
  filename: string,
  signal?: AbortSignal,
): Promise<{ filename: string; deleted: boolean }> {
  return request<{ filename: string; deleted: boolean }>(`/system-messages/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
    signal,
  });
}

export async function downloadFile(url: string, signal?: AbortSignal): Promise<Blob> {
  const response = await fetch(url, { signal });
  return handleResponse<Blob>(response);
}


export interface TopFoldersResponse {
  folders: string[];
}


export async function getTopFolders(signal?: AbortSignal): Promise<TopFoldersResponse> {
  return request<TopFoldersResponse>('/files/top-folders', { signal });
}

export async function getSettings(signal?: AbortSignal): Promise<SettingsResponse> {
  return request<SettingsResponse>('/settings', { signal });
}

export async function updateSettingsEnv(
  updates: Record<string, string>,
  signal?: AbortSignal,
): Promise<{ [key: string]: boolean }> {
  return request<{ [key: string]: boolean }>('/settings/env', {
    method: 'PUT',
    body: { updates },
    signal,
  });
}
