import type { ChangeEvent } from 'react';

import { ActionButton } from './ActionButton';
import type { HeaderAction, SystemMessageOption, ThemeName } from '../types';
import {
  Brain,
  FolderOpen,
  Info,
  Moon,
  Play,
  PlusSquare,
  Save,
  Settings,
  Sun,
  Upload,
} from 'lucide-react';

type HeaderProps = {
  models: string[];
  systemMessages: SystemMessageOption[];
  selectedModel: string;
  selectedSystemMessage: string;
  onModelChange: (model: string) => void;
  onSystemMessageChange: (systemId: string) => void;
  onAction: (action: HeaderAction) => void;
  themeName: ThemeName;
  sendDisabled?: boolean;
};

export function Header({
  models,
  systemMessages,
  selectedModel,
  selectedSystemMessage,
  onModelChange,
  onSystemMessageChange,
  onAction,
  themeName,
  sendDisabled: _sendDisabled = false,
}: HeaderProps) {
  const handleModelChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onModelChange(event.target.value);
  };

  const handleSystemMessageChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onSystemMessageChange(event.target.value);
  };

  const isDark = themeName === 'dark';
  const themeLabel = isDark ? 'Light Theme' : 'Dark Theme';
  const themeIcon = isDark ? <Sun size={18} /> : <Moon size={18} />;

  return (
    <header className="app-header">
      <div className="header-top">
        <h1 className="app-title">
          <span className="emoji" role="img" aria-hidden="true">
            <Brain size={22} />
          </span>
          CodeWhisper
        </h1>

        <div className="header-selections">
          <div className="selection-control">
            <label htmlFor="model-select">Model:</label>
            <select id="model-select" value={selectedModel} onChange={handleModelChange}>
              {models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          <div className="selection-control">
            <label htmlFor="system-select">System:</label>
            <select
              id="system-select"
              value={selectedSystemMessage}
              onChange={handleSystemMessageChange}
            >
              {systemMessages.map((option) => (
                <option key={option.id} value={option.id} title={option.description ?? ''}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="header-actions">
        <div className="primary-actions">
          <ActionButton
            variant="accent"
            icon={<FolderOpen size={16} />}
            onClick={() => onAction('onSetContext')}
            title="Choose files to include as conversation context"
          >
            Set Context
          </ActionButton>
          <ActionButton
            variant="accent"
            icon={<Play size={16} />}
            onClick={() => onAction('onExecuteSystem')}
            title="Run the currently selected system prompt"
          >
            Execute System Prompt
          </ActionButton>
          <ActionButton
            icon={<PlusSquare size={16} />}
            onClick={() => onAction('onNewConversation')}
            title="Start a fresh conversation tab"
          >
            New Conversation
          </ActionButton>
        </div>

        <div className="secondary-actions">
          <ActionButton
            icon={<Save size={16} />}
            onClick={() => onAction('onSaveHistory')}
            title="Export the current conversation history"
          >
            Save History
          </ActionButton>
          <ActionButton
            icon={<Upload size={16} />}
            onClick={() => onAction('onLoadHistory')}
            title="Load a saved conversation history"
          >
            Load History
          </ActionButton>
          <ActionButton
            icon={<Settings size={16} />}
            onClick={() => onAction('onOpenSettings')}
            title="Open application settings"
          >
            Settings
          </ActionButton>
          <ActionButton
            icon={themeIcon}
            onClick={() => onAction('onToggleTheme')}
            title="Toggle between light and dark themes"
          >
            {themeLabel}
          </ActionButton>
          <ActionButton
            icon={<Brain size={16} />}
            onClick={() => onAction('onOpenSystemMessage')}
            title="Review or edit the system message library"
          >
            System Message
          </ActionButton>
          <ActionButton
            icon={<Info size={16} />}
            onClick={() => onAction('onOpenAbout')}
            title="View application information"
          >
            About
          </ActionButton>
        </div>
      </div>
    </header>
  );
}
