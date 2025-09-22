import type { CSSProperties, ReactNode } from 'react';
import { X } from 'lucide-react';

type ModalProps = {
  title: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  width?: string;
  height?: string;
  style?: CSSProperties;
};

export function Modal({ title, isOpen, onClose, children, footer, width, height, style }: ModalProps) {
  if (!isOpen) {
    return null;
  }

  const modalStyle = {
    width,
    height,
    ...style
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal" style={modalStyle}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer ? <div className="modal-footer">{footer}</div> : null}
      </div>
    </div>
  );
}
