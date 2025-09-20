
import {
  type ChangeEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import './App.css';
import { Header } from './components/Header';
import { InputPanel } from './components/InputPanel';
import { StatusBar } from './components/StatusBar';
import { TabManager } from './components/TabManager';
import { AboutModal, ContextModal, SettingsModal, SystemMessageModal } from './components/modals';
import {
  askQuestion,
  clearConversation,
  createConversation,
  deleteConversation,
  exportConversation,
  fetchSystemMessageContent,
  fetchUiDefaults,
  importConversation,
  runSystemPrompt,
  setConversationApiKey,
  setConversationModel,
  setDirectory,
  setSystemMessage,
  toggleTheme,
  updateSelectedFiles,
} from './api';
import type {
  ChatMessage,
  CodebaseFile,
  ConversationCreateResponse,
  ConversationSummary,
  QuickCommand,
  QuestionStatus,
  SystemMessageOption,
  SystemMessageRecord,
  ThemeName,
  UiDefaultsResponse,
} from './types';

const FALLBACK_MODELS: string[] = [
  'openrouter/anthropic/claude-3.5-sonnet',
  'openrouter/openai/gpt-4o-mini',
  'openrouter/google/gemini-flash-1.5',
  'openrouter/meta/llama-3.1-70b',
];

const FALLBACK_SYSTEM_MESSAGES: SystemMessageOption[] = [
  {
    id: 'default',
    label: 'Default',
    description: 'General purpose instructions for Code Chat conversations.',
  },
];

const FALLBACK_TOOL_COMMANDS: QuickCommand[] = [
  { key: 'TOOL_SCAN', value: 'scan --depth=2 --include *.py' },
  { key: 'TOOL_TEST', value: 'venv/Scripts/python.exe -m pytest tests/ -q' },
  { key: 'TOOL_LOGS', value: 'tail -n 200 logs/structured.log' },
  { key: 'TOOL_DOCS', value: 'open README.md --section getting-started' },
];

interface ConversationTabState {
  id: string;
  title: string;
  createdAt: string;
  dirty: boolean;
  conversationId: string;
  summary: ConversationSummary;
  messages: ChatMessage[];
  availableModels: string[];
}


const formatTimestamp = (input?: string) => {
  if (!input) {
    return new Date().toLocaleTimeString();
  }
  const parsed = new Date(input);
  if (Number.isNaN(parsed.getTime())) {
    return input;
  }
  return parsed.toLocaleTimeString();
};

const buildMessagesFromSummary = (summary: ConversationSummary): ChatMessage[] => {
  const messages: ChatMessage[] = [];
  const questions: QuestionStatus[] = summary.questionHistory ?? [];
  let questionIndex = 0;

  summary.conversationHistory.forEach((entry, index) => {
    let timestamp = formatTimestamp();
    let tokensUsed: number | undefined;
    let processingTime: number | undefined;
    let modelUsed: string | undefined;

    if (entry.role === 'user') {
      const info = questions[questionIndex];
      if (info) {
        timestamp = formatTimestamp(info.timestamp);
      }
    } else if (entry.role === 'assistant') {
      const info = questions[questionIndex] ?? questions[Math.max(0, questionIndex - 1)];
      if (info) {
        timestamp = formatTimestamp(info.timestamp);
        tokensUsed = info.tokensUsed;
        processingTime = info.processingTime;
        modelUsed = info.modelUsed;
      }
      if (questions[questionIndex]) {
        questionIndex += 1;
      }
    }

    messages.push({
      id: `${summary.conversationId}-${index}`,
      role: entry.role,
      content: entry.content,
      timestamp,
      tokensUsed,
      processingTime,
      modelUsed,
    });
  });

  return messages;
};

const createTabStateFromResponse = (
  response: ConversationCreateResponse,
  title: string,
): ConversationTabState => ({
  id: response.conversationId,
  title,
  createdAt: new Date().toISOString(),
  dirty: false,
  conversationId: response.conversationId,
  summary: response.summary,
  messages: buildMessagesFromSummary(response.summary),
  availableModels: response.availableModels,
});

const downloadJson = (data: unknown, filename: string) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

const truncatePath = (value: string, max = 48) => {
  if (value.length <= max) {
    return value;
  }
  const start = value.slice(0, Math.floor(max / 2));
  const end = value.slice(-Math.floor(max / 2));
  return `${start}...${end}`;
};

function App() {
  const [tabs, setTabs] = useState<ConversationTabState[]>([]);
  const [activeTabId, setActiveTabId] = useState('');
  const [tabCounter, setTabCounter] = useState(0);

  const [themeName, setThemeName] = useState<ThemeName>('light');
  const [statusMessage, setStatusMessage] = useState('Loading defaults from server...');
  const [statusType, setStatusType] = useState<'info' | 'success' | 'warning' | 'error'>('info');

  const [toolCommands, setToolCommands] = useState<QuickCommand[]>(FALLBACK_TOOL_COMMANDS);
  const [systemMessageOptions, setSystemMessageOptions] = useState<SystemMessageOption[]>(FALLBACK_SYSTEM_MESSAGES);
  const [systemMessageRecords, setSystemMessageRecords] = useState<SystemMessageRecord[]>([]);
  const [selectedSystemMessage, setSelectedSystemMessage] = useState(
    FALLBACK_SYSTEM_MESSAGES[0]?.id ?? 'default',
  );
  const [models, setModels] = useState<string[]>(FALLBACK_MODELS);
  const [apiKey, setApiKey] = useState('');

  const [questionDraft, setQuestionDraft] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [contextModalOpen, setContextModalOpen] = useState(false);
  const [contextDirectory, setContextDirectory] = useState('');
  const [contextFiles, setContextFiles] = useState<CodebaseFile[]>([]);
  const [contextSelectedFiles, setContextSelectedFiles] = useState<string[]>([]);
  const [contextPersistent, setContextPersistent] = useState(false);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const [contextMessage, setContextMessage] = useState('');

  const [systemMessageModalOpen, setSystemMessageModalOpen] = useState(false);
  const [systemMessageSelection, setSystemMessageSelection] = useState('');
  const [systemMessagePreview, setSystemMessagePreview] = useState('');
  const [systemMessageLoading, setSystemMessageLoading] = useState(false);
  const [systemMessageError, setSystemMessageError] = useState<string | null>(null);

  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);

  const [aboutModalOpen, setAboutModalOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const defaultsLoadedRef = useRef(false);

  const updateStatus = useCallback(
    (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
      setStatusMessage(message);
      setStatusType(type);
    },
    [],
  );

  const activeTab = useMemo(
    () => tabs.find((tab) => tab.id === activeTabId) ?? tabs[0] ?? null,
    [tabs, activeTabId],
  );

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.dataset.theme = themeName;
    }
  }, [themeName]);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const fallbackRecords: SystemMessageRecord[] = FALLBACK_SYSTEM_MESSAGES.map((option) => ({
      filename: option.id,
      display_name: option.label,
      preview: option.description ?? '',
      length: option.description?.length ?? 0,
      is_current: option.id === selectedSystemMessage,
    }));

    const initialise = async () => {
      try {
        const defaults: UiDefaultsResponse = await fetchUiDefaults(controller.signal);
        if (cancelled) {
          return;
        }

        const availableModels = defaults.models.length > 0 ? defaults.models : FALLBACK_MODELS;
        const availableCommands: QuickCommand[] = defaults.toolCommands.length > 0
          ? defaults.toolCommands.map((item) => ({ key: item.key, value: item.value }))
          : FALLBACK_TOOL_COMMANDS;

        const systemRecords = defaults.systemMessages.messages.length > 0
          ? defaults.systemMessages.messages
          : fallbackRecords;

        const systemOptions: SystemMessageOption[] = systemRecords.map((record) => ({
          id: record.filename,
          label: record.display_name || record.filename,
          description: record.preview,
        }));

        setSystemMessageRecords(systemRecords);
        setSystemMessageOptions(systemOptions);
        setSelectedSystemMessage(
          defaults.systemMessages.current || systemOptions[0]?.id || FALLBACK_SYSTEM_MESSAGES[0]?.id || 'default',
        );
        setToolCommands(availableCommands);
        setModels(availableModels);
        setApiKey(defaults.apiKey ?? '');

        const conversation = await createConversation(
          {
            provider: defaults.provider,
            model: defaults.defaultModel || availableModels[0],
            apiKey: defaults.apiKey,
          },
          controller.signal,
        );

        if (cancelled) {
          return;
        }

        const title = 'Chat 1';
        const tab = createTabStateFromResponse(conversation, title);
        setTabs([tab]);
        setActiveTabId(tab.id);
        setTabCounter(1);
        updateStatus('Ready.');
        defaultsLoadedRef.current = true;
      } catch (error) {
        if (cancelled) {
          return;
        }

        updateStatus(`Failed to load defaults: ${String(error)}`, 'warning');
        setSystemMessageRecords(fallbackRecords);
        setSystemMessageOptions(FALLBACK_SYSTEM_MESSAGES);
        setToolCommands(FALLBACK_TOOL_COMMANDS);
        setModels(FALLBACK_MODELS);
        setSelectedSystemMessage(FALLBACK_SYSTEM_MESSAGES[0]?.id ?? 'default');

        try {
          const conversation = await createConversation(
            {
              model: FALLBACK_MODELS[0],
              apiKey,
            },
            controller.signal,
          );
          if (cancelled) {
            return;
          }
          const title = 'Chat 1';
          const tab = createTabStateFromResponse(conversation, title);
          setTabs([tab]);
          setActiveTabId(tab.id);
          setTabCounter(1);
          updateStatus('Ready.');
          defaultsLoadedRef.current = true;
        } catch (creationError) {
          updateStatus(`Unable to create conversation: ${String(creationError)}`, 'error');
        }
      }
    };

    initialise();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [apiKey, selectedSystemMessage, updateStatus]);

  const updateTabSummaryState = useCallback(
    (conversationId: string, summary: ConversationSummary, dirty = true) => {
      setTabs((previous) =>
        previous.map((tab) =>
          tab.conversationId === conversationId
            ? {
                ...tab,
                dirty,
                summary,
                messages: buildMessagesFromSummary(summary),
              }
            : tab,
        ),
      );
    },
    [],
  );

  const updateTabFromResponse = useCallback(
    (response: ConversationCreateResponse, dirty = true) => {
      setTabs((previous) =>
        previous.map((tab) =>
          tab.conversationId === response.conversationId
            ? {
                ...tab,
                dirty,
                summary: response.summary,
                messages: buildMessagesFromSummary(response.summary),
                availableModels: response.availableModels,
              }
            : tab,
        ),
      );
      if (response.conversationId === activeTabId) {
        setModels(response.availableModels.length > 0 ? response.availableModels : FALLBACK_MODELS);
      }
    },
    [activeTabId],
  );

  const handleModelChange = useCallback(
    async (model: string) => {
      const tab = activeTab;
      if (!tab || tab.summary.selectedModel === model) {
        return;
      }
      try {
        updateStatus('Updating model...', 'info');
        const response = await setConversationModel(tab.conversationId, model);
        updateTabFromResponse(response, true);
        updateStatus(`Model switched to ${response.model}.`, 'success');
      } catch (error) {
        updateStatus(`Failed to update model: ${String(error)}`, 'error');
      }
    },
    [activeTab, updateStatus, updateTabFromResponse],
  );

  const handleSystemMessageChange = useCallback(
    async (systemId: string) => {
      if (!systemId || systemId === selectedSystemMessage) {
        return;
      }
      try {
        await setSystemMessage(systemId);
        setSelectedSystemMessage(systemId);
        setSystemMessageRecords((previous) =>
          previous.map((record) => ({ ...record, is_current: record.filename === systemId })),
        );
        updateStatus('System message updated.', 'success');
      } catch (error) {
        updateStatus(`Failed to update system message: ${String(error)}`, 'error');
      }
    },
    [selectedSystemMessage, updateStatus],
  );

  const handleSendQuestion = useCallback(async () => {
    const tab = activeTab;
    const trimmed = questionDraft.trim();
    if (!tab) {
      updateStatus('Create a conversation before sending a question.', 'warning');
      return;
    }
    if (trimmed.length === 0) {
      updateStatus('Add a question before sending it to the assistant.', 'warning');
      return;
    }
    if (!defaultsLoadedRef.current || (tab.summary.questionHistory.length === 0 && tab.summary.selectedFiles.length === 0)) {
      updateStatus('Select at least one file in the context before asking your first question.', 'warning');
      return;
    }

    try {
      setIsSubmitting(true);
      updateStatus('Question sent. Waiting for the assistant...', 'info');
      const response = await askQuestion(tab.conversationId, { question: trimmed });
      updateTabSummaryState(tab.conversationId, response.summary, true);
      setQuestionDraft('');
      updateStatus(
        `Assistant reply received in ${response.processingTime.toFixed(2)}s (${response.tokensUsed} tokens).`,
        'success',
      );
    } catch (error) {
      updateStatus(`Unable to send question: ${String(error)}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  }, [activeTab, questionDraft, updateStatus, updateTabSummaryState]);

  const handleToggleTheme = useCallback(async () => {
    try {
      const result = await toggleTheme();
      const nextTheme = (result.theme as ThemeName) ?? (themeName === 'light' ? 'dark' : 'light');
      setThemeName(nextTheme);
      if (typeof document !== 'undefined') {
        document.documentElement.dataset.theme = nextTheme;
      }
      updateStatus(result.message || 'Theme updated.', 'success');
    } catch (error) {
      updateStatus(`Failed to toggle theme: ${String(error)}`, 'error');
    }
  }, [themeName, updateStatus]);

  const handleOpenContext = useCallback(() => {
    const tab = activeTab;
    if (!tab) {
      updateStatus('Create a conversation before setting context.', 'warning');
      return;
    }
    setContextDirectory(tab.summary.selectedDirectory || '');
    setContextFiles([]);
    setContextSelectedFiles(tab.summary.selectedFiles);
    setContextPersistent(tab.summary.persistentFiles.length > 0);
    setContextMessage('');
    setContextError(null);
    setContextModalOpen(true);
  }, [activeTab, updateStatus]);

  const handleLoadDirectory = useCallback(async () => {
    const tab = activeTab;
    if (!tab) {
      return;
    }
    const directory = contextDirectory.trim();
    if (!directory) {
      setContextError('Enter a directory path to scan.');
      return;
    }
    try {
      setContextLoading(true);
      setContextError(null);
      const response = await setDirectory(tab.conversationId, directory);
      setContextFiles(response.files);
      setContextSelectedFiles(response.summary.selectedFiles);
      setContextPersistent(response.summary.persistentFiles.length > 0);
      setContextMessage(response.message);
      updateTabSummaryState(tab.conversationId, response.summary, true);
      updateStatus(response.message || 'Context updated.', 'success');
    } catch (error) {
      setContextError(String(error));
      updateStatus(`Failed to load directory: ${String(error)}`, 'error');
    } finally {
      setContextLoading(false);
    }
  }, [activeTab, contextDirectory, updateStatus, updateTabSummaryState]);

  const handleCloseContextModal = useCallback(() => {
    setContextModalOpen(false);
    setContextError(null);
    setContextMessage('');
  }, []);

  const handleToggleContextPersistent = useCallback((value: boolean) => {
    setContextPersistent(value);
  }, []);

  const handleToggleContextFile = useCallback((filePath: string) => {
    setContextSelectedFiles((previous) => {
      if (previous.includes(filePath)) {
        return previous.filter((entry) => entry !== filePath);
      }
      return [...previous, filePath];
    });
  }, []);

  const handleApplyContext = useCallback(async () => {
    const tab = activeTab;
    if (!tab) {
      return;
    }
    try {
      setContextLoading(true);
      const summary = await updateSelectedFiles(tab.conversationId, contextSelectedFiles, contextPersistent);
      updateTabSummaryState(tab.conversationId, summary, true);
      updateStatus(`Selected ${contextSelectedFiles.length} file(s) for context.`, 'success');
      handleCloseContextModal();
    } catch (error) {
      setContextError(String(error));
      updateStatus(`Failed to update selected files: ${String(error)}`, 'error');
    } finally {
      setContextLoading(false);
    }
  }, [activeTab, contextPersistent, contextSelectedFiles, handleCloseContextModal, updateStatus, updateTabSummaryState]);

  const handleClearResponse = useCallback(async () => {
    const tab = activeTab;
    if (!tab) {
      return;
    }
    try {
      const summary = await clearConversation(tab.conversationId);
      updateTabSummaryState(tab.conversationId, summary, true);
      updateStatus('Conversation cleared.', 'success');
    } catch (error) {
      updateStatus(`Failed to clear conversation: ${String(error)}`, 'error');
    }
  }, [activeTab, updateStatus, updateTabSummaryState]);

  const handleRunSystemPrompt = useCallback(async () => {
    const tab = activeTab;
    if (!tab) {
      return;
    }
    try {
      updateStatus('Running system prompt...', 'info');
      const response = await runSystemPrompt(tab.conversationId);
      updateTabSummaryState(tab.conversationId, response.summary, true);
      updateStatus(
        `System prompt executed in ${response.processingTime.toFixed(2)}s (${response.tokensUsed} tokens).`,
        'success',
      );
    } catch (error) {
      updateStatus(`System prompt failed: ${String(error)}`, 'error');
    }
  }, [activeTab, updateStatus, updateTabSummaryState]);

  const handleNewConversation = useCallback(async () => {
    const provider = activeTab?.summary.provider;
    const model = activeTab?.summary.selectedModel || models[0];
    try {
      updateStatus('Starting new conversation...', 'info');
      const response = await createConversation({ provider, model, apiKey });
      const nextCounter = tabCounter + 1;
      const title = `Chat ${nextCounter}`;
      const newTab = createTabStateFromResponse(response, title);
      setTabs((previous) => [...previous, newTab]);
      setActiveTabId(newTab.id);
      setTabCounter(nextCounter);
      setModels(response.availableModels.length > 0 ? response.availableModels : FALLBACK_MODELS);
      updateStatus(`${title} ready.`, 'success');
    } catch (error) {
      updateStatus(`Failed to start conversation: ${String(error)}`, 'error');
    }
  }, [activeTab, apiKey, models, tabCounter, updateStatus]);

  const handleSelectTab = useCallback(
    (tabId: string) => {
      setActiveTabId(tabId);
      const tab = tabs.find((entry) => entry.id === tabId);
      if (tab) {
        setModels(tab.availableModels.length > 0 ? tab.availableModels : FALLBACK_MODELS);
        updateStatus(`Switched to ${tab.title}.`, 'info');
      }
    },
    [tabs, updateStatus],
  );

  const handleCloseTab = useCallback(
    async (tabId: string) => {
      const tab = tabs.find((entry) => entry.id === tabId);
      if (!tab) {
        return;
      }
      if (tabs.length <= 1) {
        updateStatus('Cannot close the last tab.', 'warning');
        return;
      }
      try {
        await deleteConversation(tab.conversationId);
      } catch {
        // ignore errors when removing server-side session
      }
      setTabs((previous) => previous.filter((entry) => entry.id !== tabId));
      setActiveTabId((current) => (current === tabId ? '' : current));
      updateStatus(`${tab.title} closed.`, 'info');
    },
    [tabs, updateStatus],
  );

  useEffect(() => {
    if (!activeTabId && tabs.length > 0) {
      setActiveTabId(tabs[0].id);
    }
  }, [activeTabId, tabs]);

  const handleSaveHistory = useCallback(async () => {
    const tab = activeTab;
    if (!tab) {
      return;
    }
    try {
      const exported = await exportConversation(tab.conversationId);
      downloadJson(exported, `${tab.title.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.json`);
      updateTabSummaryState(tab.conversationId, exported.summary, false);
      updateStatus('Conversation exported.', 'success');
    } catch (error) {
      updateStatus(`Failed to export conversation: ${String(error)}`, 'error');
    }
  }, [activeTab, updateStatus, updateTabSummaryState]);

  const handleLoadHistory = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleHistoryFileChange = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }
      try {
        const text = await file.text();
        const payload = JSON.parse(text);
        const response = await importConversation(payload);
        const nextCounter = tabCounter + 1;
        const title = `Imported Chat ${nextCounter}`;
        const newTab = createTabStateFromResponse(response, title);
        setTabs((previous) => [...previous, newTab]);
        setActiveTabId(newTab.id);
        setTabCounter(nextCounter);
        setModels(response.availableModels.length > 0 ? response.availableModels : FALLBACK_MODELS);
        updateStatus('Conversation imported.', 'success');
      } catch (error) {
        updateStatus(`Failed to import conversation: ${String(error)}`, 'error');
      } finally {
        event.target.value = '';
      }
    },
    [tabCounter, updateStatus],
  );

  const handleSystemMessageModalOpen = useCallback(() => {
    const initialSelection = selectedSystemMessage || systemMessageOptions[0]?.id || '';
    setSystemMessageSelection(initialSelection);
    setSystemMessagePreview('');
    setSystemMessageError(null);
    setSystemMessageModalOpen(true);
  }, [selectedSystemMessage, systemMessageOptions]);

  const handleSystemMessageModalClose = useCallback(() => {
    setSystemMessageModalOpen(false);
    setSystemMessageError(null);
    setSystemMessagePreview('');
  }, []);

  useEffect(() => {
    const loadPreview = async () => {
      if (!systemMessageModalOpen || !systemMessageSelection) {
        return;
      }
      setSystemMessageLoading(true);
      setSystemMessageError(null);
      try {
        const result = await fetchSystemMessageContent(systemMessageSelection);
        setSystemMessagePreview(result.content);
      } catch (error) {
        setSystemMessageError(String(error));
      } finally {
        setSystemMessageLoading(false);
      }
    };

    loadPreview();
  }, [systemMessageModalOpen, systemMessageSelection]);

  const applySystemMessageSelection = useCallback(async () => {
    if (!systemMessageSelection) {
      return;
    }
    try {
      await setSystemMessage(systemMessageSelection);
      setSelectedSystemMessage(systemMessageSelection);
      setSystemMessageRecords((previous) =>
        previous.map((record) => ({ ...record, is_current: record.filename === systemMessageSelection })),
      );
      updateStatus('System message updated.', 'success');
      handleSystemMessageModalClose();
    } catch (error) {
      setSystemMessageError(String(error));
      updateStatus(`Failed to apply system message: ${String(error)}`, 'error');
    }
  }, [handleSystemMessageModalClose, systemMessageSelection, updateStatus]);

  const handleSettingsModalClose = useCallback(() => {
    setSettingsModalOpen(false);
    setSettingsError(null);
  }, []);

  const handleSettingsSave = useCallback(async () => {
    const tab = activeTab;
    if (!tab) {
      return;
    }
    try {
      setSettingsSaving(true);
      setSettingsError(null);
      const response = await setConversationApiKey(tab.conversationId, apiKeyInput.trim());
      updateTabFromResponse(response, true);
      setApiKey(apiKeyInput.trim());
      updateStatus('API key updated.', 'success');
      handleSettingsModalClose();
    } catch (error) {
      setSettingsError(String(error));
      updateStatus(`Failed to update API key: ${String(error)}`, 'error');
    } finally {
      setSettingsSaving(false);
    }
  }, [activeTab, apiKeyInput, handleSettingsModalClose, updateStatus, updateTabFromResponse]);

  const badges = useMemo(() => {
    if (!activeTab) {
      return [] as string[];
    }
    const provider = activeTab.summary.provider || 'n/a';
    const model = activeTab.summary.selectedModel || 'n/a';
    const directory = activeTab.summary.selectedDirectory
      ? truncatePath(activeTab.summary.selectedDirectory)
      : 'none';
    const filesCount = activeTab.summary.selectedFiles.length;
    return [
      `Provider: ${provider}`,
      `Model: ${model}`,
      `Directory: ${directory}`,
      `Files: ${filesCount}`,
    ];
  }, [activeTab]);

  const toolCommandOptions = toolCommands.length > 0 ? toolCommands : FALLBACK_TOOL_COMMANDS;
  const modelsForHeader = activeTab ? activeTab.availableModels : models;
  const selectedModel = activeTab?.summary.selectedModel || modelsForHeader[0] || '';

  const headerActions = useMemo(() => ({
    onSetContext: handleOpenContext,
    onSendQuestion: handleSendQuestion,
    onExecuteSystem: handleRunSystemPrompt,
    onClearResponse: handleClearResponse,
    onNewConversation: handleNewConversation,
    onSaveHistory: handleSaveHistory,
    onLoadHistory: handleLoadHistory,
    onOpenSettings: () => {
      setApiKeyInput(apiKey);
      setSettingsError(null);
      setSettingsModalOpen(true);
    },
    onToggleTheme: handleToggleTheme,
    onOpenSystemMessage: handleSystemMessageModalOpen,
    onOpenAbout: () => setAboutModalOpen(true),
  }), [
    apiKey,
    handleClearResponse,
    handleLoadHistory,
    handleNewConversation,
    handleOpenContext,
    handleRunSystemPrompt,
    handleSaveHistory,
    handleSendQuestion,
    handleSystemMessageModalOpen,
    handleToggleTheme,
  ]);

  const tabsForView = tabs.map((tab) => ({
    id: tab.id,
    title: tab.title,
    dirty: tab.dirty,
    messages: tab.messages,
  }));

  const canSubmit = Boolean(questionDraft.trim()) && !isSubmitting && Boolean(activeTab);

  return (
    <div className="app-shell">
      <Header
        models={modelsForHeader}
        systemMessages={systemMessageOptions}
        selectedModel={selectedModel}
        selectedSystemMessage={selectedSystemMessage}
        onModelChange={handleModelChange}
        onSystemMessageChange={handleSystemMessageChange}
        onAction={(action) => headerActions[action]()}
        themeName={themeName}
        sendDisabled={!canSubmit}
      />

      <main className="main-content">
        <TabManager
          tabs={tabsForView}
          activeTabId={activeTab?.id ?? ''}
          onSelectTab={handleSelectTab}
          onNewTab={handleNewConversation}
          onCloseTab={handleCloseTab}
          onSaveTab={handleSaveHistory}
        />

        <InputPanel
          value={questionDraft}
          onChange={setQuestionDraft}
          onSubmit={handleSendQuestion}
          onClear={() => setQuestionDraft('')}
          toolCommands={toolCommandOptions}
          isSubmitting={isSubmitting}
        />
      </main>

      <StatusBar message={statusMessage} statusType={statusType} badges={badges} />

      <input
        type="file"
        ref={fileInputRef}
        accept="application/json"
        style={{ display: 'none' }}
        onChange={handleHistoryFileChange}
      />

      <ContextModal
        isOpen={contextModalOpen}
        directory={contextDirectory}
        message={contextMessage}
        error={contextError}
        isLoading={contextLoading}
        files={contextFiles}
        selectedFiles={contextSelectedFiles}
        persistent={contextPersistent}
        onClose={handleCloseContextModal}
        onDirectoryChange={setContextDirectory}
        onTogglePersistent={handleToggleContextPersistent}
        onToggleFile={handleToggleContextFile}
        onLoadDirectory={handleLoadDirectory}
        onApply={handleApplyContext}
      />

      <SystemMessageModal
        isOpen={systemMessageModalOpen}
        records={systemMessageRecords}
        selectedId={systemMessageSelection}
        preview={systemMessagePreview}
        isLoading={systemMessageLoading}
        error={systemMessageError}
        onClose={handleSystemMessageModalClose}
        onSelect={setSystemMessageSelection}
        onApply={applySystemMessageSelection}
      />

      <SettingsModal
        isOpen={settingsModalOpen}
        apiKey={apiKeyInput}
        isSaving={settingsSaving}
        error={settingsError}
        onClose={handleSettingsModalClose}
        onChangeApiKey={setApiKeyInput}
        onSave={handleSettingsSave}
      />

      <AboutModal isOpen={aboutModalOpen} onClose={() => setAboutModalOpen(false)} />
    </div>
  );
}

export default App;
