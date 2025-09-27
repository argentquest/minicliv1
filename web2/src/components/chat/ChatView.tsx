import React, { useRef, useEffect, useState } from 'react';
import { Card, Button, Typography, Tag, Space, Tooltip } from 'antd';
import {
  ExpandOutlined,
  CompressOutlined,
  CopyOutlined,
  DownloadOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../../types';

const { Text, Paragraph } = Typography;

interface MessageItemProps {
  message: Message;
  onExtractCode?: (messageId: string) => void;
  onRenderMermaid?: (code: string) => void;
}

const MessageItem: React.FC<MessageItemProps> = ({ 
  message, 
  onExtractCode, 
  onRenderMermaid 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showFullContent, setShowFullContent] = useState(false);
  
  const isLongContent = message.content.length > 1000;
  const shouldTruncate = isLongContent && !showFullContent;
  const displayContent = shouldTruncate 
    ? message.content.substring(0, 1000) + '...' 
    : message.content;

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getMessageStyle = () => {
    switch (message.role) {
      case 'system':
        return {
          backgroundColor: '#fff7e6',
          borderColor: '#ffd666',
          borderLeft: '4px solid #faad14',
        };
      case 'user':
        return {
          backgroundColor: '#e6f7ff',
          borderColor: '#91d5ff',
          borderLeft: '4px solid #1890ff',
        };
      case 'assistant':
        return {
          backgroundColor: '#ffffff',
          borderColor: '#d9d9d9',
          borderLeft: '4px solid #52c41a',
        };
      default:
        return {};
    }
  };

  const handleCopyContent = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      // Could add a toast notification here
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  const detectCodeBlocks = (content: string) => {
    // Use exact same pattern as web1: /```(\w+)?\n([\s\S]*?)\n```/g
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)\n```/g;
    const matches = [];
    let match;
    
    while ((match = codeBlockRegex.exec(content)) !== null) {
      matches.push({
        language: match[1] || 'text',
        code: match[2],
        fullMatch: match[0],
      });
    }
    
    return matches;
  };
  
  const hasCodeFragments = (content: string): boolean => {
    // Use exact same detection as web1: /```[\s\S]*?```/.test(text)
    return /```[\s\S]*?```/.test(content);
  };

  const detectMermaidDiagrams = (content: string) => {
    const mermaidRegex = /```mermaid\n([\s\S]*?)```/g;
    const matches = [];
    let match;
    
    while ((match = mermaidRegex.exec(content)) !== null) {
      matches.push(match[1]);
    }
    
    return matches;
  };

  const codeBlocks = detectCodeBlocks(message.content);
  const mermaidDiagrams = detectMermaidDiagrams(message.content);

  return (
    <Card
      className="mb-4 message-card"
      style={getMessageStyle()}
      size="small"
    >
      {/* Message Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Tag color={
            message.role === 'system' ? 'orange' :
            message.role === 'user' ? 'blue' : 'green'
          }>
            {message.role.toUpperCase()}
          </Tag>
          <Text type="secondary" className="text-xs">
            {formatTimestamp(message.timestamp)}
          </Text>
          {message.metadata?.model && (
            <Text type="secondary" className="text-xs">
              ({message.metadata.model})
            </Text>
          )}
          {message.metadata?.tokens && (
            <Text type="secondary" className="text-xs">
              {message.metadata.tokens} tokens
            </Text>
          )}
        </div>
        
        <Space>
          {/* Extract Code Button */}
          {hasCodeFragments(message.content) && onExtractCode && (
            <Tooltip title={`Extract ${codeBlocks.length} code block(s)`}>
              <Button
                type="text"
                size="small"
                icon={<CodeOutlined />}
                onClick={() => onExtractCode(message.id)}
              />
            </Tooltip>
          )}
          
          {/* Render Mermaid Button */}
          {mermaidDiagrams.length > 0 && onRenderMermaid && (
            <Tooltip title={`Render ${mermaidDiagrams.length} diagram(s)`}>
              <Button
                type="text"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => mermaidDiagrams.forEach(diagram => onRenderMermaid?.(diagram))}
              />
            </Tooltip>
          )}
          
          {/* Copy Button */}
          <Tooltip title="Copy content">
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={handleCopyContent}
            />
          </Tooltip>
          
          {/* Expand/Collapse Button */}
          <Tooltip title={isExpanded ? "Collapse" : "Expand"}>
            <Button
              type="text"
              size="small"
              icon={isExpanded ? <CompressOutlined /> : <ExpandOutlined />}
              onClick={() => setIsExpanded(!isExpanded)}
            />
          </Tooltip>
        </Space>
      </div>

      {/* Message Content */}
      {isExpanded && (
        <div className="message-content">
          <div className="prose dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <pre
                      className={`${className} bg-gray-50 dark:bg-gray-800 p-4 rounded overflow-x-auto`}
                      {...props}
                    >
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  ) : (
                    <code className={`${className} bg-gray-100 dark:bg-gray-700 px-1 rounded`} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {displayContent}
            </ReactMarkdown>
          </div>
          
          {/* Show More/Less for long content */}
          {isLongContent && (
            <div className="mt-4 text-center">
              <Button
                type="link"
                onClick={() => setShowFullContent(!showFullContent)}
                size="small"
              >
                {showFullContent ? 'Show Less' : 'Show More'}
              </Button>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

interface ChatViewProps {
  messages: Message[];
  loading?: boolean;
  onExtractCode?: (messageId: string) => void;
  onRenderMermaid?: (code: string) => void;
}

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  loading = false,
  onExtractCode,
  onRenderMermaid,
}) => {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">💬</div>
          <Typography.Title level={3} className="!text-gray-500">
            Start your first conversation
          </Typography.Title>
          <Typography.Text type="secondary">
            Type a question below to begin chatting with the AI assistant.
          </Typography.Text>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            onExtractCode={onExtractCode}
            onRenderMermaid={onRenderMermaid}
          />
        ))}
        
        {loading && (
          <Card className="mb-4" style={{
            backgroundColor: '#ffffff',
            borderColor: '#d9d9d9',
            borderLeft: '4px solid #52c41a',
          }}>
            <div className="flex items-center gap-2">
              <Tag color="green">ASSISTANT</Tag>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </Card>
        )}
        
        <div ref={chatEndRef} />
      </div>
    </div>
  );
};

export default ChatView;