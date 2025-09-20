import { useState } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';
import type { ChatMessage } from '../types';

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

  const toggleCollapse = (messageId: string) => {
    setCollapsedMap((previous) => {
      const next = { ...previous };
      if (next[messageId]) {
        delete next[messageId];
      } else {
        next[messageId] = true;
      }
      return next;
    });
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
                <strong>{ROLE_LABEL[message.role]}</strong>
                <span>{message.timestamp}</span>
              </div>
              <button
                type="button"
                className="chat-message__toggle"
                aria-label={isCollapsed ? 'Expand message' : 'Collapse message'}
                aria-expanded={!isCollapsed}
                onClick={() => toggleCollapse(message.id)}
              >
                {isCollapsed ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
              </button>
            </header>

            {isCollapsed ? (
              <div className="chat-message__body chat-message__body--collapsed">{COLLAPSED_PLACEHOLDER}</div>
            ) : (
              <>
                <div className="chat-message__body">{message.content}</div>

                {badgeParts.length > 0 ? (
                  <div className="chat-message__meta">{badgeParts.join(' | ')}</div>
                ) : null}

                {message.contextFiles && message.contextFiles.length > 0 ? (
                  <div className="chat-context-files">
                    {message.contextFiles.map((file) => (
                      <span key={file} className="chat-context-chip">
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
  );
}
