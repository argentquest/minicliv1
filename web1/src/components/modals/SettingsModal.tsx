import type { ChangeEvent } from 'react';
import { useState, useEffect } from 'react';
import { Loader2, Save } from 'lucide-react';

import { ActionButton } from '../ActionButton';
import { Modal } from './Modal';
import { getSettings, updateSettingsEnv } from '../../api';
import type { SettingsResponse } from '../../types';

type SettingsModalProps = {
  isOpen: boolean;
  isSaving: boolean;
  error: string | null;
  onClose: () => void;
  onSave: () => void;
};

export function SettingsModal({
  isOpen,
  isSaving,
  error,
  onClose,
  onSave,
}: SettingsModalProps) {
  const [settings, setSettings] = useState<SettingsResponse>({ values: {}, masked: {}, descriptions: {}, theme: '', availableThemes: [] });
  const [changes, setChanges] = useState<Record<string, string>>({});
  const [localError, setLocalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setLocalError(null);
      getSettings()
        .then((response) => {
          setSettings(response);
          setChanges({});
        })
        .catch((err: unknown) => {
          setLocalError('Failed to load settings');
          console.error('Settings load error:', err);
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  const handleInputChange = (key: string, event: ChangeEvent<HTMLInputElement>) => {
    setChanges(prev => ({ ...prev, [key]: event.target.value }));
  };

  const handleSave = async () => {
    if (Object.keys(changes).length === 0) {
      onClose();
      return;
    }

    setLoading(true);
    setLocalError(null);
    try {
      const response = await updateSettingsEnv(changes);
      if (response) {
        // Update local settings with successful changes
        setSettings(prev => ({
          ...prev,
          values: { ...prev.values, ...changes },
          masked: { ...prev.masked, ...Object.fromEntries(Object.entries(changes).map(([k, v]) => [k, k.includes('KEY') ? '***' : v])) }
        }));
        setChanges({});
        onSave();
      }
    } catch (err: unknown) {
      setLocalError('Failed to save settings');
      console.error('Settings save error:', err);
    } finally {
      setLoading(false);
    }
  };

  const footer = (
    <>
      <ActionButton onClick={onClose} disabled={loading || isSaving}>
        Cancel
      </ActionButton>
      <ActionButton
        variant="primary"
        icon={loading || isSaving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
        onClick={handleSave}
        disabled={loading || isSaving || Object.keys(changes).length === 0}
      >
        {loading || isSaving ? 'Saving...' : 'Save Settings'}
      </ActionButton>
    </>
  );

  if (loading) {
    return (
      <Modal title="Environment Settings" isOpen={isOpen} onClose={onClose} footer={footer} width="600px">
        <div className="flex justify-center py-4">
          <Loader2 size={24} className="spin" />
        </div>
      </Modal>
    );
  }

  return (
    <Modal title="Environment Settings" isOpen={isOpen} onClose={onClose} footer={footer} width="600px">
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {Object.entries(settings.values).map(([key, value]) => {
          const description = settings.descriptions[key] || key;
          const isSensitive = key.includes('KEY') || key.includes('TOKEN') || key.includes('PASSWORD');
          const currentValue = changes[key] !== undefined ? changes[key] : value;
          const displayValue = settings.masked[key] || currentValue;

          return (
            <div key={key} className="form-group relative">
              <label htmlFor={`env-${key}`}>{description}</label>
              <input
                id={`env-${key}`}
                type={isSensitive ? 'password' : 'text'}
                value={currentValue as string}
                onChange={(e) => handleInputChange(key, e)}
                placeholder={`Enter ${key}`}
                autoComplete="off"
                disabled={loading || isSaving}
                className={isSensitive ? 'pr-8' : ''}
              />
              {isSensitive && (
                <span className="absolute right-3 top-10 text-muted">{displayValue}</span>
              )}
              <p className="text-xs text-muted mt-1">{description}</p>
            </div>
          );
        })}
      </div>
      {(localError || error) ? (
        <div className="context-error mt-4" role="alert">
          {localError || error}
        </div>
      ) : null}
      <p className="muted text-xs mt-4">
        Changes are saved to .env file and take effect on restart. Sensitive values are masked for security.
      </p>
    </Modal>
  );
}
