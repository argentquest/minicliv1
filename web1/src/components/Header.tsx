import type { ChangeEvent } from 'react';

import { ActionButton } from './ActionButton';
import type { HeaderAction, SystemMessageOption, ThemeName } from '../types';
import {
  Brain,
  Eraser,
  FolderOpen,
  Info,
  Moon,
  Play,
  PlusSquare,
  Save,
  Send,
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
  sendDisabled = false,
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
          Code Chat with AI
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
          >
            Set Context
          </ActionButton>
          <ActionButton
            variant="primary"
            icon={<Send size={16} />}
            onClick={() => onAction('onSendQuestion')}
            disabled={sendDisabled}
          >
            Send Question
          </ActionButton>
          <ActionButton
            variant="accent"
            icon={<Play size={16} />}
            onClick={() => onAction('onExecuteSystem')}
          >
            Execute System Prompt
          </ActionButton>
          <ActionButton icon={<Eraser size={16} />} onClick={() => onAction('onClearResponse')}>
            Clear Response
          </ActionButton>
          <ActionButton icon={<PlusSquare size={16} />} onClick={() => onAction('onNewConversation')}>
            New Conversation
          </ActionButton>
        </div>

        <div className="secondary-actions">
          <ActionButton icon={<Save size={16} />} onClick={() => onAction('onSaveHistory')}>
            Save History
          </ActionButton>
          <ActionButton icon={<Upload size={16} />} onClick={() => onAction('onLoadHistory')}>
            Load History
          </ActionButton>
          <ActionButton icon={<Settings size={16} />} onClick={() => onAction('onOpenSettings')}>
            Settings
          </ActionButton>
          <ActionButton icon={themeIcon} onClick={() => onAction('onToggleTheme')}>
            {themeLabel}
          </ActionButton>
          <ActionButton icon={<Brain size={16} />} onClick={() => onAction('onOpenSystemMessage')}>
            System Message
          </ActionButton>
          <ActionButton icon={<Info size={16} />} onClick={() => onAction('onOpenAbout')}>
            About
          </ActionButton>
        </div>
      </div>
    </header>
  );
}
