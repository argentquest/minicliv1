import React, { useState, useRef, useEffect } from 'react';
import { Button, Input, Select, Space, Tooltip, Dropdown } from 'antd';
import {
  SendOutlined,
  ClearOutlined,
  PlusOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { TextArea } = Input;
const { Option } = Select;

interface InputPanelProps {
  onSendMessage: (message: string, command?: string) => void;
  onClear: () => void;
  loading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export const InputPanel: React.FC<InputPanelProps> = ({
  onSendMessage,
  onClear,
  loading = false,
  placeholder = "Type your next question. Press Enter to send, Shift+Enter for a new line.",
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const [selectedCommand, setSelectedCommand] = useState<string>('');
  const textAreaRef = useRef<any>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textAreaRef.current && textAreaRef.current.resizableTextArea) {
      textAreaRef.current.resizableTextArea.resizeTextarea?.();
    }
  }, [message]);

  const quickCommands = [
    { label: 'EXPLAIN', value: 'explain', description: 'Explain this code in detail' },
    { label: 'REFACTOR', value: 'refactor', description: 'Refactor and improve this code' },
    { label: 'DEBUG', value: 'debug', description: 'Find and fix bugs in this code' },
    { label: 'DOCUMENT', value: 'document', description: 'Generate documentation' },
    { label: 'OPTIMIZE', value: 'optimize', description: 'Optimize performance' },
    { label: 'TEST', value: 'test', description: 'Generate unit tests' },
    { label: 'REVIEW', value: 'review', description: 'Code review and suggestions' },
    { label: 'CONVERT', value: 'convert', description: 'Convert to another language/format' },
  ];

  const handleSend = () => {
    if (message.trim() && !loading) {
      onSendMessage(message.trim(), selectedCommand);
      setMessage('');
      setSelectedCommand('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMessage('');
    setSelectedCommand('');
    onClear();
  };

  const insertCommand = (command: string) => {
    const commandText = quickCommands.find(cmd => cmd.value === command)?.label || command;
    const newMessage = message ? `${message}\n\n${commandText}: ` : `${commandText}: `;
    setMessage(newMessage);
    setSelectedCommand(command);
    
    // Focus textarea after inserting command
    setTimeout(() => {
      textAreaRef.current?.focus();
      textAreaRef.current?.resizeTextArea();
    }, 0);
  };

  const commandMenuItems: MenuProps['items'] = quickCommands.map(cmd => ({
    key: cmd.value,
    label: (
      <div>
        <div className="font-semibold">{cmd.label}</div>
        <div className="text-xs text-gray-500">{cmd.description}</div>
      </div>
    ),
    onClick: () => insertCommand(cmd.value),
  }));

  const recentPrompts = [
    "Explain this function step by step",
    "How can I optimize this code?",
    "Generate unit tests for this component",
    "What are the potential bugs here?",
    "Convert this to TypeScript",
  ];

  const recentMenuItems: MenuProps['items'] = recentPrompts.map((prompt, index) => ({
    key: index.toString(),
    label: prompt,
    onClick: () => setMessage(prompt),
  }));

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Quick Commands Row */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
            Quick Commands:
          </span>
          
          <Select
            placeholder="EXPLAIN"
            value={selectedCommand}
            onChange={setSelectedCommand}
            className="min-w-[120px]"
            size="small"
            allowClear
          >
            {quickCommands.map(cmd => (
              <Option key={cmd.value} value={cmd.value}>
                {cmd.label}
              </Option>
            ))}
          </Select>

          <Dropdown menu={{ items: commandMenuItems }} placement="topLeft">
            <Button size="small" icon={<PlusOutlined />}>
              Insert Command
            </Button>
          </Dropdown>

          <Dropdown menu={{ items: recentMenuItems }} placement="topLeft">
            <Button size="small" icon={<HistoryOutlined />}>
              Recent
            </Button>
          </Dropdown>

          <div className="flex-1" />

          <Tooltip title="Explain this code in detail, including its purpose and how it works">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Explain this code in detail, including its purpose and how it works:
            </span>
          </Tooltip>
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <div className="flex-1">
            <TextArea
              ref={textAreaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled || loading}
              autoSize={{ minRows: 2, maxRows: 8 }}
              className="resize-none"
            />
          </div>

          <div className="flex flex-col gap-2">
            <Tooltip title="Submit Question">
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={loading}
                disabled={!message.trim() || disabled}
                className="!bg-purple-600 !border-purple-600 hover:!bg-purple-700"
              >
                Submit Question
              </Button>
            </Tooltip>

            <Tooltip title="Clear">
              <Button
                icon={<ClearOutlined />}
                onClick={handleClear}
                disabled={loading}
              >
                Clear
              </Button>
            </Tooltip>
          </div>
        </div>

        {/* Helper Text */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          Press Enter to send • Shift+Enter for new line • Use quick commands for better results
        </div>
      </div>
    </div>
  );
};

export default InputPanel;