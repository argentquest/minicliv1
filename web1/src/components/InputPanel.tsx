import { useEffect, useMemo, useState, type ChangeEvent, type KeyboardEvent } from 'react';

import { ActionButton } from './ActionButton';
import { ClipboardList, Loader2, Send, Trash2 } from 'lucide-react';
import type { QuickCommand } from '../types';

type InputPanelProps = {
  value: string;
  onChange: (nextValue: string) => void;
  onSubmit: () => void;
  onClear: () => void;
  toolCommands: QuickCommand[];
  isSubmitting?: boolean;
};

export function InputPanel({
  value,
  onChange,
  onSubmit,
  onClear,
  toolCommands,
  isSubmitting = false,
}: InputPanelProps) {
  const [selectedKey, setSelectedKey] = useState<string>('');

  useEffect(() => {
    if (toolCommands.length === 0) {
      setSelectedKey('');
      return;
    }
    if (!toolCommands.some((command) => command.key === selectedKey)) {
      setSelectedKey(toolCommands[0].key);
    }
  }, [toolCommands, selectedKey]);

  const selectedCommand = useMemo(
    () => toolCommands.find((command) => command.key === selectedKey),
    [toolCommands, selectedKey],
  );

  const previewText = useMemo(() => {
    if (!selectedCommand) {
      return 'No quick command selected';
    }
    const { value: commandText } = selectedCommand;
    return commandText.length > 100 ? `${commandText.slice(0, 100)}…` : commandText;
  }, [selectedCommand]);

  const handleTextareaChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(event.target.value);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.ctrlKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  const handleToolInsert = () => {
    if (!selectedCommand) {
      return;
    }
    const commandValue = selectedCommand.value;
    const insertion = value.trim().length > 0 ? `${value}\n${commandValue}` : commandValue;
    onChange(`${insertion}\n`);
  };

  const isSubmitDisabled = value.trim().length === 0 || isSubmitting;

  return (
    <section className="input-panel" aria-label="Question input">
      <div className="tool-row">
        <label htmlFor="tool-select">Quick Commands:</label>
        <select
          id="tool-select"
          className="tool-select"
          value={selectedKey}
          onChange={(event) => setSelectedKey(event.target.value)}
          disabled={toolCommands.length === 0}
        >
          {toolCommands.length === 0 ? (
            <option value="">No TOOL variables available</option>
          ) : null}
          {toolCommands.map((command) => (
            <option key={command.key} value={command.key}>
              {command.key.replace(/^TOOL[_-]?/, '')}
            </option>
          ))}
        </select>
        <ActionButton
          icon={<ClipboardList size={16} />}
          onClick={handleToolInsert}
          disabled={!selectedCommand}
        >
          Insert Command
        </ActionButton>
        <p className="tool-preview" aria-live="polite">
          {previewText}
        </p>
      </div>

      <div className="input-row">
        <textarea
          className="question-textarea"
          placeholder="Type your next question. Press Enter to send, Shift+Enter for a new line."
          value={value}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
        />
        <div className="button-column">
          <ActionButton
            variant="primary"
            icon={isSubmitting ? <Loader2 className="spin" size={16} /> : <Send size={16} />}
            onClick={onSubmit}
            disabled={isSubmitDisabled}
          >
            {isSubmitting ? 'Sending…' : 'Submit Question'}
          </ActionButton>
          <ActionButton icon={<Trash2 size={16} />} onClick={onClear} disabled={value.trim().length === 0}>
            Clear
          </ActionButton>
        </div>
      </div>
    </section>
  );
}
