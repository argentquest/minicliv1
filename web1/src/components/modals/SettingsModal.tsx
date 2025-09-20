import type { ChangeEvent } from 'react';
import { Loader2, Save } from 'lucide-react';

import { ActionButton } from '../ActionButton';
import { Modal } from './Modal';

type SettingsModalProps = {
  isOpen: boolean;
  apiKey: string;
  isSaving: boolean;
  error: string | null;
  onClose: () => void;
  onChangeApiKey: (value: string) => void;
  onSave: () => void;
};

export function SettingsModal({
  isOpen,
  apiKey,
  isSaving,
  error,
  onClose,
  onChangeApiKey,
  onSave,
}: SettingsModalProps) {
  const handleApiKeyChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChangeApiKey(event.target.value);
  };

  const footer = (
    <>
      <ActionButton onClick={onClose} disabled={isSaving}>
        Cancel
      </ActionButton>
      <ActionButton
        variant="primary"
        icon={isSaving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
        onClick={onSave}
        disabled={isSaving}
      >
        {isSaving ? 'Saving...' : 'Save Settings'}
      </ActionButton>
    </>
  );

  return (
    <Modal title="Conversation Settings" isOpen={isOpen} onClose={onClose} footer={footer} width="520px">
      <div className="form-group">
        <label htmlFor="api-key-input">API Key</label>
        <input
          id="api-key-input"
          type="password"
          value={apiKey}
          onChange={handleApiKeyChange}
          placeholder="Enter provider API key"
          autoComplete="off"
          disabled={isSaving}
        />
      </div>
      <p className="muted">
        The API key is stored in memory for the current session. Use environment variables for persistent storage.
      </p>
      {error ? (
        <div className="context-error" role="alert">
          {error}
        </div>
      ) : null}
    </Modal>
  );
}
