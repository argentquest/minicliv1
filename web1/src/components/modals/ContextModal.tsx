import type { ChangeEvent } from 'react';
import { Loader2, RefreshCcw } from 'lucide-react';

import { ActionButton } from '../ActionButton';
import type { CodebaseFile } from '../../types';
import { Modal } from './Modal';

type ContextModalProps = {
  isOpen: boolean;
  directory: string;
  message: string;
  error: string | null;
  isLoading: boolean;
  files: CodebaseFile[];
  selectedFiles: string[];
  persistent: boolean;
  onClose: () => void;
  onDirectoryChange: (value: string) => void;
  onTogglePersistent: (value: boolean) => void;
  onToggleFile: (value: string) => void;
  onLoadDirectory: () => void;
  onApply: () => void;
};

export function ContextModal({
  isOpen,
  directory,
  message,
  error,
  isLoading,
  files,
  selectedFiles,
  persistent,
  onClose,
  onDirectoryChange,
  onTogglePersistent,
  onToggleFile,
  onLoadDirectory,
  onApply,
}: ContextModalProps) {
  const handleDirectoryChange = (event: ChangeEvent<HTMLInputElement>) => {
    onDirectoryChange(event.target.value);
  };

  const footer = (
    <>
      <ActionButton onClick={onClose} disabled={isLoading}>
        Cancel
      </ActionButton>
      <ActionButton
        variant="primary"
        onClick={onApply}
        disabled={isLoading || selectedFiles.length === 0}
      >
        Apply Context
      </ActionButton>
    </>
  );

  const renderFileList = () => {
    if (isLoading) {
      return (
        <div className="context-info" aria-live="polite">
          <Loader2 size={16} className="spin" /> Loading files...
        </div>
      );
    }

    if (files.length === 0) {
      return <p className="muted">No files available for the selected directory.</p>;
    }

    return (
      <div className="context-file-list">
        {files.map((file) => {
          const value = file.relativePath || file.path;
          const isChecked = selectedFiles.includes(value);
          return (
            <label key={value} className={isChecked ? 'context-file--selected' : ''}>
              <input
                type="checkbox"
                checked={isChecked}
                disabled={isLoading}
                onChange={() => onToggleFile(value)}
              />
              <span>{value}</span>
            </label>
          );
        })}
      </div>
    );
  };

  return (
    <Modal title="Conversation Context" isOpen={isOpen} onClose={onClose} footer={footer} width="720px">
      <div className="form-group">
        <label htmlFor="context-directory">Directory Path</label>
        <div className="modal-actions-inline">
          <input
            id="context-directory"
            type="text"
            value={directory}
            onChange={handleDirectoryChange}
            placeholder="e.g. src/app"
            disabled={isLoading}
          />
          <ActionButton
            icon={isLoading ? <Loader2 size={16} className="spin" /> : <RefreshCcw size={16} />}
            onClick={onLoadDirectory}
            disabled={isLoading || directory.trim().length === 0}
          >
            {isLoading ? 'Loading...' : 'Load Directory'}
          </ActionButton>
        </div>
      </div>

      <div className="checkbox-inline">
        <input
          id="context-persistent"
          type="checkbox"
          checked={persistent}
          disabled={isLoading}
          onChange={(event) => onTogglePersistent(event.target.checked)}
        />
        <label htmlFor="context-persistent">Persist selected files across questions</label>
      </div>

      {error ? (
        <div className="context-error" role="alert">
          {error}
        </div>
      ) : null}
      {message ? <div className="context-info">{message}</div> : null}

      {renderFileList()}
    </Modal>
  );
}
