import type { ChangeEvent } from 'react';
import { BookOpen } from 'lucide-react';

import { ActionButton } from '../ActionButton';
import type { SystemMessageRecord } from '../../types';
import { Modal } from './Modal';

type SystemMessageModalProps = {
  isOpen: boolean;
  records: SystemMessageRecord[];
  selectedId: string;
  preview: string;
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
  onSelect: (id: string) => void;
  onApply: () => void;
};

export function SystemMessageModal({
  isOpen,
  records,
  selectedId,
  preview,
  isLoading,
  error,
  onClose,
  onSelect,
  onApply,
}: SystemMessageModalProps) {
  const handleSelectionChange = (event: ChangeEvent<HTMLInputElement>) => {
    onSelect(event.target.value);
  };

  const footer = (
    <>
      <ActionButton onClick={onClose} disabled={isLoading}>
        Cancel
      </ActionButton>
      <ActionButton
        variant="primary"
        onClick={onApply}
        disabled={isLoading || !selectedId}
      >
        Use System Message
      </ActionButton>
    </>
  );

  return (
    <Modal title="System Messages" isOpen={isOpen} onClose={onClose} footer={footer} width="760px">
      {error ? (
        <div className="context-error" role="alert">
          {error}
        </div>
      ) : null}

      <div className="system-message-list" role="radiogroup" aria-label="System message templates">
        {records.length === 0 ? <p className="muted">No system messages found.</p> : null}
        {records.map((record) => {
          const value = record.filename;
          const label = record.display_name || record.filename;
          const isSelected = value === selectedId;
          const itemClasses = ['system-message-item'];
          if (isSelected) {
            itemClasses.push('system-message-item--selected');
          }
          return (
            <label key={value} className={itemClasses.join(' ')}>
              <div className="system-message-item__header">
                <input
                  type="radio"
                  name="system-message"
                  value={value}
                  checked={isSelected}
                  disabled={isLoading}
                  onChange={handleSelectionChange}
                />
                <div className="system-message-item__title">
                  <span>{label}</span>
                  {record.is_current ? (
                    <span className="badge" aria-label="Currently active system message">
                      Current
                    </span>
                  ) : null}
                </div>
              </div>
              <p className="system-message-item__preview" title={record.preview}>
                {record.preview || 'No preview available.'}
              </p>
            </label>
          );
        })}
      </div>

      <div className="form-group">
        <label htmlFor="system-message-preview">Preview</label>
        <textarea
          id="system-message-preview"
          className="system-message-content"
          value={isLoading ? 'Loading preview...' : preview}
          readOnly
        />
      </div>

      <p className="muted" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <BookOpen size={16} />
        System messages help steer the assistant before the first user prompt.
      </p>
    </Modal>
  );
}
