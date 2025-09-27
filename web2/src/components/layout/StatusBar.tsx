import React from 'react';
import { Space, Tag, Typography, Tooltip, Button } from 'antd';
import {
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  CloudOutlined,
  ApiOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface StatusBarProps {
  status: 'ready' | 'loading' | 'error';
  provider?: string;
  model?: string;
  directory?: string;
  fileCount?: number;
  tokenCount?: number;
  onOpenDirectory?: () => void;
  errorMessage?: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  status,
  provider = 'openrouter',
  model = 'x-ai/grok-code-fast-1',
  directory = 'none',
  fileCount = 0,
  tokenCount = 0,
  onOpenDirectory,
  errorMessage,
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'ready':
        return <CheckCircleOutlined className="text-green-500" />;
      case 'loading':
        return <LoadingOutlined className="text-blue-500" />;
      case 'error':
        return <ExclamationCircleOutlined className="text-red-500" />;
      default:
        return <CheckCircleOutlined className="text-gray-500" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'ready':
        return 'Ready';
      case 'loading':
        return 'Processing...';
      case 'error':
        return errorMessage || 'Error';
      default:
        return 'Unknown';
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  return (
    <div className="h-8 bg-gray-100 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 flex items-center justify-between text-xs">
      {/* Left Section - Status */}
      <Space size="large">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <Text className="text-xs font-medium">
            {getStatusText()}
          </Text>
        </div>

        {/* Provider Information */}
        <Tooltip title={`Provider: ${provider}`}>
          <div className="flex items-center gap-1">
            <CloudOutlined className="text-gray-500" />
            <Text className="text-xs text-gray-600 dark:text-gray-400">
              Provider: {provider}
            </Text>
          </div>
        </Tooltip>

        {/* Model Information */}
        <Tooltip title={`Active model: ${model}`}>
          <div className="flex items-center gap-1">
            <ApiOutlined className="text-gray-500" />
            <Text className="text-xs text-gray-600 dark:text-gray-400">
              Model: {model}
            </Text>
          </div>
        </Tooltip>
      </Space>

      {/* Right Section - Context & Stats */}
      <Space size="large">
        {/* Token Count */}
        {tokenCount > 0 && (
          <Tooltip title={`Total tokens in conversation: ${tokenCount.toLocaleString()}`}>
            <Tag className="text-xs">
              {formatNumber(tokenCount)} tokens
            </Tag>
          </Tooltip>
        )}

        {/* File Count & Directory */}
        <div className="flex items-center gap-2">
          <Tooltip title={`${fileCount} files in context`}>
            <div className="flex items-center gap-1">
              <FileTextOutlined className="text-gray-500" />
              <Text className="text-xs text-gray-600 dark:text-gray-400">
                Files: {fileCount}
              </Text>
            </div>
          </Tooltip>

          <Tooltip title={`Current directory: ${directory}`}>
            <Button
              type="text"
              size="small"
              className="!p-0 !h-auto"
              onClick={onOpenDirectory}
            >
              <div className="flex items-center gap-1">
                <FolderOpenOutlined className="text-gray-500" />
                <Text className="text-xs text-gray-600 dark:text-gray-400 max-w-[200px] truncate">
                  Directory: {directory}
                </Text>
              </div>
            </Button>
          </Tooltip>
        </div>
      </Space>
    </div>
  );
};

export default StatusBar;