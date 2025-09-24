import { ExternalLink } from 'lucide-react';

import { ActionButton } from '../ActionButton';
import { Modal } from './Modal';

type AboutModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function AboutModal({ isOpen, onClose }: AboutModalProps) {
  const footer = (
    <ActionButton onClick={onClose}>Close</ActionButton>
  );

  return (
    <Modal title="About WhisperCode" isOpen={isOpen} onClose={onClose} footer={footer} width="480px">
      <p>
        WhisperCode is a local-first interface for exploring your codebase with AI assistance. The desktop client connects with
        your configured model provider and keeps conversation context in sync with the selected files from your workspace.
      </p>
      <p>
        Use the context panel to set directories or individual files, run quick commands from the toolbar, and export
        conversations when you are ready to share results with your team.
      </p>
      <p>
        Created by <a href="https://github.com/argentquest" target="_blank" rel="noopener noreferrer">Eric Silver</a> of Argent Quest Inc.
    
      </p>
      <p className="muted" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ExternalLink size={16} /> Refer to README.md for setup, or CLI_USAGE.md for offline workflows.
      </p>
    </Modal>
  );
}
