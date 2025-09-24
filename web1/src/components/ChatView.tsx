import { useState, useEffect } from 'react';
import { Maximize2, Minimize2, Code, Eye, EyeOff } from 'lucide-react';
import type { ChatMessage } from '../types';
import { CodeFragmentsModal } from './modals/CodeFragmentsModal';

type ChatViewProps = {
  messages: ChatMessage[];
};

const ROLE_LABEL: Record<ChatMessage['role'], string> = {
  user: 'You',
  assistant: 'AI Assistant',
  system: 'System',
};

const COLLAPSED_PLACEHOLDER = 'Message collapsed. Expand to view full content.';

export function ChatView({ messages }: ChatViewProps) {
  const [collapsedMap, setCollapsedMap] = useState<Record<string, boolean>>({});
  const [markdownToggles, setMarkdownToggles] = useState<Record<string, boolean>>({});
  const [codeModalOpen, setCodeModalOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<ChatMessage | null>(null);

  useEffect(() => {
    setCollapsedMap((prev) => {
      const updated = { ...prev };
      messages.forEach((message) => {
        if (updated[message.id] === undefined) {
          updated[message.id] = message.role === 'system';
        }
      });
      return updated;
    });
    setMarkdownToggles((prev) => {
      const updated = { ...prev };
      messages.forEach((message) => {
        if (updated[message.id] === undefined) {
          updated[message.id] = true;
        }
      });
      return updated;
    });
  }, [messages]);

  const hasCodeFragments = (message: ChatMessage): boolean => {
    const text = message.rawMarkdown || message.content;
    return /```[\s\S]*?```/.test(text);
  };

  const openCodeModal = (message: ChatMessage) => {
    setSelectedMessage(message);
    setCodeModalOpen(true);
  };

  const closeCodeModal = () => {
    setCodeModalOpen(false);
    setSelectedMessage(null);
  };

  const toggleCollapse = (messageId: string) => {
    setCollapsedMap((previous) => ({
      ...previous,
      [messageId]: !previous[messageId]
    }));
  };

  const toggleMarkdown = (messageId: string) => {
    setMarkdownToggles((previous) => ({
      ...previous,
      [messageId]: !previous[messageId]
    }));
  };

  const stripHtml = (html: string): string => {
    return html
      .replace(/<[^>]*>/g, '')
      .replace(/&nbsp;/g, ' ')
      .replace(/&/g, '&')
      .replace(/</g, '<')
      .replace(/>/g, '>')
      .replace(/"/g, '"')
      .trim();
  };

  if (messages.length === 0) {
    return (
      <section className="chat-view" aria-label="Conversation transcript">
        <div className="chat-message chat-message--system" role="note">
          <div className="chat-message__body">
            Start your first conversation by writing a question below. We will render replies here as soon as the assistant responds.
          </div>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="chat-view" aria-label="Conversation transcript">
        {messages.map((message) => {
          const roleClass = `chat-message--${message.role}`;
          const badgeParts: string[] = [];
          const isCollapsed = Boolean(collapsedMap[message.id]);

          if (message.tokensUsed) {
            badgeParts.push(`${message.tokensUsed} tokens`);
          }
          if (message.processingTime) {
            badgeParts.push(`${message.processingTime.toFixed(1)}s`);
          }
          if (message.modelUsed) {
            badgeParts.push(message.modelUsed.split('/').pop() ?? message.modelUsed);
          }

          return (
            <article key={message.id} className={`chat-message ${roleClass}`}>
              <header className="chat-message__header">
                <div className="chat-message__header-info">
                  <strong title={`${ROLE_LABEL[message.role]} message`}>{ROLE_LABEL[message.role]}</strong>
                  <span title="Message timestamp">{message.timestamp}</span>
                </div>
                <div className="chat-message__actions">
                  {message.role === 'assistant' && hasCodeFragments(message) && (
                    <button
                      type="button"
                      className="chat-message__code-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        openCodeModal(message);
                      }}
                      title="View code fragments"
                      aria-label="View code fragments"
                    >
                      <Code size={16} />
                    </button>
                  )}
                  {message.role === 'assistant' && (
                    <button
                      type="button"
                      className="chat-message__markdown-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleMarkdown(message.id);
                      }}
                      title={markdownToggles[message.id] ? 'Show raw Markdown' : 'Show formatted HTML'}
                      aria-label={markdownToggles[message.id] ? 'Show raw Markdown' : 'Show formatted HTML'}
                    >
                      {markdownToggles[message.id] ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  )}
                  <button
                    type="button"
                    className="chat-message__toggle"
                    title={isCollapsed ? 'Expand message' : 'Collapse message'}
                    aria-label={isCollapsed ? 'Expand message' : 'Collapse message'}
                    aria-expanded={!isCollapsed}
                    onClick={() => toggleCollapse(message.id)}
                  >
                    {isCollapsed ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
                  </button>
                </div>
              </header>

              {isCollapsed ? (
                <div className="chat-message__body chat-message__body--collapsed">{COLLAPSED_PLACEHOLDER}</div>
              ) : (
                <>
                  <div className="chat-message__body">
                    {message.role === 'assistant' ? (
                      markdownToggles[message.id] ? (
                        <div dangerouslySetInnerHTML={{ __html: message.content }} />
                      ) : (
                        <div>{message.rawMarkdown || stripHtml(message.content)}</div>
                      )
                    ) : (
                      <div>{message.content}</div>
                    )}
                  </div>
                  
                  {badgeParts.length > 0 ? (
                    <div className="chat-message__meta">
                      {badgeParts.map((badge, index) => {
                        let title = '';
                        if (badge.includes('tokens')) {
                          title = 'Tokens used in response generation';
                        } else if (badge.includes('s')) {
                          title = 'Processing time';
                        } else {
                          title = 'Model used';
                        }
                        return (
                          <span key={index} title={title} className="chat-message__badge">
                            {badge}
                          </span>
                        );
                      })}
                    </div>
                  ) : null}
                  
                  {message.contextFiles && message.contextFiles.length > 0 ? (
                    <div className="chat-context-files">
                      {message.contextFiles.map((file) => (
                        <span key={file} className="chat-context-chip" title={`Context file: ${file}`}>
                          {file}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </>
              )}
            </article>
          );
        })}
      </section>
      {selectedMessage && (
        <CodeFragmentsModal
          isOpen={codeModalOpen}
          message={selectedMessage}
          onClose={closeCodeModal}
        />
      )}
    </>
  );
}
