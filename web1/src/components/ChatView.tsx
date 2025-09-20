import type { ChatMessage } from '../types';

type ChatViewProps = {
  messages: ChatMessage[];
};

const ROLE_LABEL: Record<ChatMessage['role'], string> = {
  user: 'You',
  assistant: 'AI Assistant',
  system: 'System',
};

export function ChatView({ messages }: ChatViewProps) {
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
              <strong>{ROLE_LABEL[message.role]}</strong>
              <span>{message.timestamp}</span>
            </header>

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
          </article>
        );
      })}
    </section>
  );
}
