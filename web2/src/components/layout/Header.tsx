import React, { useState } from 'react';
import { Layout, Button, Select, Space, Typography, Tooltip } from 'antd';
import {
  MoonOutlined,
  SunOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  MessageOutlined,
  SaveOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  BookOutlined,
  PlayCircleOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { useTheme } from '../../themes';

const { Header: AntHeader } = Layout;
const { Title } = Typography;
const { Option } = Select;

interface HeaderProps {
  onSetContext: () => void;
  onExecuteSystemPrompt: () => void;
  onNewConversation: () => void;
  onSaveHistory: () => void;
  onLoadHistory: () => void;
  onOpenSettings: () => void;
  onToggleTheme: () => void;
  onSystemMessage: () => void;
  onAbout: () => void;
  onCodeFragments: () => void;
  currentModel?: string;
  onModelChange: (model: string) => void;
  currentSystem?: string;
  onSystemChange: (system: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  onSetContext,
  onExecuteSystemPrompt,
  onNewConversation,
  onSaveHistory,
  onLoadHistory,
  onOpenSettings,
  onToggleTheme,
  onSystemMessage,
  onAbout,
  onCodeFragments,
  currentModel = 'x-ai/grok-code-fast-1',
  onModelChange,
  currentSystem = 'default',
  onSystemChange,
}) => {
  const { theme } = useTheme();

  const modelOptions = [
    'x-ai/grok-code-fast-1',
    'anthropic/claude-3-sonnet',
    'openai/gpt-4-turbo',
    'google/gemini-pro',
    'meta/llama-2-70b',
  ];

  const systemOptions = [
    'default',
    'coding',
    'documentation',
    'refactoring',
    'debugging',
  ];

  const documentationOptions = [
    { label: 'API Reference', value: 'api' },
    { label: 'User Guide', value: 'guide' },
    { label: 'Examples', value: 'examples' },
    { label: 'FAQ', value: 'faq' },
  ];

  return (
    <AntHeader className="!px-6 !h-16 flex items-center justify-between bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      {/* Left Section - Branding */}
      <div className="flex items-center">
        <Title level={3} className="!mb-0 !text-gray-800 dark:!text-white">
          🧠 WhisperCode
        </Title>
      </div>

      {/* Center Section - Dropdowns */}
      <div className="flex items-center gap-4">
        {/* Model Selection */}
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 mb-1">Model:</span>
          <Select
            value={currentModel}
            onChange={onModelChange}
            className="min-w-[200px]"
            size="small"
          >
            {modelOptions.map(model => (
              <Option key={model} value={model}>{model}</Option>
            ))}
          </Select>
        </div>

        {/* System Selection */}
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 mb-1">System:</span>
          <Select
            value={currentSystem}
            onChange={onSystemChange}
            className="min-w-[120px]"
            size="small"
          >
            {systemOptions.map(system => (
              <Option key={system} value={system}>
                {system.charAt(0).toUpperCase() + system.slice(1)}
              </Option>
            ))}
          </Select>
        </div>

        {/* Documentation Dropdown */}
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 mb-1">Documentation:</span>
          <Select
            placeholder="Select docs"
            className="min-w-[120px]"
            size="small"
            allowClear
          >
            {documentationOptions.map(doc => (
              <Option key={doc.value} value={doc.value}>{doc.label}</Option>
            ))}
          </Select>
        </div>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center">
        {/* Primary Actions */}
        <Space.Compact>
          <Tooltip title="Set Context">
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              onClick={onSetContext}
              className="!bg-purple-600 !border-purple-600 hover:!bg-purple-700"
            >
              Set Context
            </Button>
          </Tooltip>
          
          <Tooltip title="Execute System Prompt">
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={onExecuteSystemPrompt}
              className="!bg-purple-600 !border-purple-600 hover:!bg-purple-700 !ml-2"
            >
              Execute System Prompt
            </Button>
          </Tooltip>
          
          <Tooltip title="New Conversation">
            <Button
              icon={<MessageOutlined />}
              onClick={onNewConversation}
              className="!ml-2"
            >
              New Conversation
            </Button>
          </Tooltip>
        </Space.Compact>

        {/* Secondary Actions */}
        <div className="flex items-center ml-4 gap-1">
          <Tooltip title="Save History">
            <Button
              type="text"
              icon={<SaveOutlined />}
              onClick={onSaveHistory}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title="Load History">
            <Button
              type="text"
              icon={<FolderOpenOutlined />}
              onClick={onLoadHistory}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title="Settings">
            <Button
              type="text"
              icon={<SettingOutlined />}
              onClick={onOpenSettings}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}>
            <Button
              type="text"
              icon={theme === 'light' ? <MoonOutlined /> : <SunOutlined />}
              onClick={onToggleTheme}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title="System Message">
            <Button
              type="text"
              icon={<BookOutlined />}
              onClick={onSystemMessage}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title="Code Fragments">
            <Button
              type="text"
              icon={<CodeOutlined />}
              onClick={onCodeFragments}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title="About">
            <Button
              type="text"
              icon={<InfoCircleOutlined />}
              onClick={onAbout}
              size="small"
            />
          </Tooltip>
        </div>
      </div>
    </AntHeader>
  );
};

export default Header;