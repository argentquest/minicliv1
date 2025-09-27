import React, { useState, useEffect } from 'react';
import { Button, Space, Typography, Input, Tag, Tooltip, message } from 'antd';
import {
  CopyOutlined,
  DownloadOutlined,
  DeleteOutlined,
  SearchOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { Modal } from '../common/Modal';
import type { CodeBlock } from '../../types';

const { Title, Text } = Typography;
const { Search } = Input;

interface CodeFragmentsModalProps {
  open: boolean;
  onCancel: () => void;
  codeBlocks: CodeBlock[];
  onDeleteBlock?: (blockId: string) => void;
  onDownloadBlock?: (block: CodeBlock) => void;
}

export const CodeFragmentsModal: React.FC<CodeFragmentsModalProps> = ({
  open,
  onCancel,
  codeBlocks,
  onDeleteBlock,
  onDownloadBlock,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');

  const filteredBlocks = codeBlocks.filter(block => {
    const matchesSearch = 
      block.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      block.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      block.language.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesLanguage = !selectedLanguage || block.language === selectedLanguage;
    
    return matchesSearch && matchesLanguage;
  });

  const languages = [...new Set(codeBlocks.map(block => block.language))].sort();

  const handleCopyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      message.success('Code copied to clipboard');
    } catch (error) {
      message.error('Failed to copy code');
    }
  };

  const handleDownload = (block: CodeBlock) => {
    const element = document.createElement('a');
    const file = new Blob([block.code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = block.filename || `code-block.${getFileExtension(block.language)}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    
    if (onDownloadBlock) {
      onDownloadBlock(block);
    }
  };

  const getFileExtension = (language: string): string => {
    const extensions: { [key: string]: string } = {
      javascript: 'js',
      typescript: 'ts',
      python: 'py',
      java: 'java',
      cpp: 'cpp',
      c: 'c',
      csharp: 'cs',
      html: 'html',
      css: 'css',
      sql: 'sql',
      bash: 'sh',
      shell: 'sh',
      json: 'json',
      xml: 'xml',
      yaml: 'yml',
      markdown: 'md',
      rust: 'rs',
      go: 'go',
      php: 'php',
      ruby: 'rb',
      swift: 'swift',
      kotlin: 'kt',
    };
    return extensions[language.toLowerCase()] || 'txt';
  };

  const getLanguageColor = (language: string): string => {
    const colors: { [key: string]: string } = {
      javascript: 'gold',
      typescript: 'blue',
      python: 'green',
      java: 'orange',
      cpp: 'purple',
      c: 'purple',
      csharp: 'purple',
      html: 'red',
      css: 'cyan',
      sql: 'geekblue',
      bash: 'lime',
      shell: 'lime',
      json: 'orange',
      xml: 'magenta',
      yaml: 'volcano',
      markdown: 'default',
      rust: 'orange',
      go: 'blue',
      php: 'purple',
      ruby: 'red',
      swift: 'orange',
      kotlin: 'purple',
    };
    return colors[language.toLowerCase()] || 'default';
  };

  const formatCode = (code: string, maxLines: number = 10): string => {
    const lines = code.split('\n');
    if (lines.length <= maxLines) {
      return code;
    }
    return lines.slice(0, maxLines).join('\n') + '\n...';
  };

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <CodeOutlined />
          <span>Code Fragments</span>
          <Tag color="blue">{codeBlocks.length} blocks</Tag>
        </div>
      }
      open={open}
      onCancel={onCancel}
      width={1000}
      footer={
        <div className="flex justify-between">
          <Text type="secondary" className="text-sm">
            {filteredBlocks.length} of {codeBlocks.length} code blocks shown
          </Text>
          <Button onClick={onCancel}>Close</Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Filters */}
        <div className="flex items-center gap-4">
          <Search
            placeholder="Search code, filename, or language..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
            allowClear
          />
          
          <div className="flex items-center gap-2">
            <Text className="whitespace-nowrap">Language:</Text>
            <div className="flex flex-wrap gap-1">
              <Tag
                className="cursor-pointer"
                color={!selectedLanguage ? 'blue' : 'default'}
                onClick={() => setSelectedLanguage('')}
              >
                All
              </Tag>
              {languages.map(language => (
                <Tag
                  key={language}
                  className="cursor-pointer"
                  color={selectedLanguage === language ? 'blue' : 'default'}
                  onClick={() => setSelectedLanguage(language === selectedLanguage ? '' : language)}
                >
                  {language}
                </Tag>
              ))}
            </div>
          </div>
        </div>

        {/* Code Blocks */}
        <div className="max-h-96 overflow-y-auto space-y-4">
          {filteredBlocks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {codeBlocks.length === 0 ? (
                <>
                  <CodeOutlined className="text-4xl mb-2" />
                  <div>No code blocks extracted yet</div>
                  <div className="text-sm">Code blocks will appear here when extracted from AI responses</div>
                </>
              ) : (
                <>No code blocks match your search criteria</>
              )}
            </div>
          ) : (
            filteredBlocks.map((block, index) => (
              <div
                key={block.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
              >
                {/* Header */}
                <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Tag color={getLanguageColor(block.language)}>
                      {block.language}
                    </Tag>
                    {block.filename && (
                      <Text className="text-sm font-mono">{block.filename}</Text>
                    )}
                    <Text type="secondary" className="text-xs">
                      {block.code.split('\n').length} lines
                    </Text>
                  </div>
                  
                  <Space>
                    <Tooltip title="Copy Code">
                      <Button
                        type="text"
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => handleCopyCode(block.code)}
                      />
                    </Tooltip>
                    
                    <Tooltip title="Download File">
                      <Button
                        type="text"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(block)}
                      />
                    </Tooltip>
                    
                    {onDeleteBlock && (
                      <Tooltip title="Delete Block">
                        <Button
                          type="text"
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={() => onDeleteBlock(block.id)}
                          danger
                        />
                      </Tooltip>
                    )}
                  </Space>
                </div>

                {/* Code Content */}
                <div className="relative">
                  <pre className="bg-gray-900 text-gray-100 p-4 overflow-x-auto text-sm font-mono max-h-60 overflow-y-auto">
                    <code>{formatCode(block.code)}</code>
                  </pre>
                  
                  {block.code.split('\n').length > 10 && (
                    <div className="absolute bottom-2 right-2">
                      <Button
                        size="small"
                        type="link"
                        onClick={() => handleCopyCode(block.code)}
                        className="!text-gray-300 hover:!text-white"
                      >
                        View Full Code
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Summary */}
        {codeBlocks.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <div>
                <Text strong>Total: {codeBlocks.length} code blocks</Text>
                <Text type="secondary" className="ml-4">
                  Languages: {languages.join(', ')}
                </Text>
              </div>
              <Space>
                <Button
                  size="small"
                  onClick={() => {
                    const allCode = codeBlocks.map(block => 
                      `// ${block.filename || 'Code Block'} (${block.language})\n${block.code}`
                    ).join('\n\n---\n\n');
                    handleCopyCode(allCode);
                  }}
                >
                  Copy All
                </Button>
              </Space>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default CodeFragmentsModal;