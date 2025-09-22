import { useState, useEffect } from 'react';
import { Clipboard, Code, X, Check } from 'lucide-react';
import { Modal } from './Modal';
import type { ChatMessage } from '../../types';

interface CodeFragment {
  language: string;
  content: string;
  preview: string;
}

interface CodeFragmentsModalProps {
  isOpen: boolean;
  message: ChatMessage;
  onClose: () => void;
}

export function CodeFragmentsModal({ isOpen, message, onClose }: CodeFragmentsModalProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [showCopied, setShowCopied] = useState(false);

  const extractFragments = (text: string): CodeFragment[] => {
    const rawText = message.rawContent || text; // Prefer raw Markdown content
    const fragments: CodeFragment[] = [];
    // Try Markdown first (on raw or fallback)
    let regex = /```(\w+)?\n([\s\S]*?)\n```/g;
    let match;
    while ((match = regex.exec(rawText)) !== null) {
      const language = match[1] || '';
      const content = match[2].trim();
      if (content) {
        const lines = content.split('\n');
        const previewLines = lines.slice(0, 3);
        let preview = previewLines.join('\n');
        if (lines.length > 3) {
          preview += '\n...';
        }
        if (language) {
          preview = `[${language}] ${preview}`;
        }
        fragments.push({ language, content, preview });
      }
    }
    // Fallback to HTML if no Markdown found
    if (fragments.length === 0) {
      regex = /<pre><code(?:\s+class="language-(\w+)")?>([\s\S]*?)<\/code><\/pre>/gi;
      while ((match = regex.exec(text)) !== null) {
        const language = match[1] || '';
        let content = match[2].trim();
        // Clean up HTML entities if any
        content = content.replace(/</g, '<').replace(/>/g, '>').replace(/&/g, '&');
        if (content) {
          const lines = content.split('\n');
          const previewLines = lines.slice(0, 3);
          let preview = previewLines.join('\n');
          if (lines.length > 3) {
            preview += '\n...';
          }
          if (language) {
            preview = `[${language}] ${preview}`;
          }
          fragments.push({ language, content, preview });
        }
      }
    }
    return fragments;
  };

  const fragments = extractFragments(message.content);
  const hasFragments = fragments.length > 0;

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setShowCopied(true);
      setTimeout(() => setShowCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  useEffect(() => {
    if (showCopied) {
      const timer = setTimeout(() => setShowCopied(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [showCopied]);

  const selectedFragment = fragments[selectedIndex] || null;

  if (!hasFragments) {
    return null;
  }

  return (
    <Modal
      title="Code Fragments"
      isOpen={isOpen}
      onClose={onClose}
      width="800px"
      height="70vh"
      footer={
        <>
          <button onClick={onClose} className="btn btn-secondary">
            <X size={16} /> Close
          </button>
        </>
      }
    >
      <div className="code-fragments-modal" style={{ position: 'relative' }}>
        {fragments.length === 0 ? (
          <p>No code fragments found.</p>
        ) : (
          <>
            <div className="fragments-list">
              {fragments.map((fragment, idx) => (
                <button
                  key={idx}
                  className={`fragment-item ${idx === selectedIndex ? 'selected' : ''}`}
                  onClick={() => setSelectedIndex(idx)}
                >
                  <Code size={16} />
                  <span>Fragment {idx + 1}: {fragment.preview}</span>
                </button>
              ))}
            </div>
            {selectedFragment && (
              <div className="fragment-preview">
                <div className="preview-header">
                  <h3>{selectedFragment.language ? `${selectedFragment.language} Code` : 'Code Fragment'}</h3>
                  <button
                    onClick={() => handleCopy(selectedFragment.content)}
                    className="copy-btn"
                    title="Copy to clipboard"
                  >
                    <Clipboard size={16} />
                  </button>
                </div>
                <pre className="preview-content">
                  <code>{selectedFragment.content}</code>
                </pre>
              </div>
            )}
          </>
        )}
        {showCopied && (
          <div className="copied-toast">
            <Check size={16} className="mr-2" />
            Copied to clipboard!
          </div>
        )}
      </div>
    </Modal>
  );
}