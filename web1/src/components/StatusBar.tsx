import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Info, OctagonX } from 'lucide-react';

type StatusType = 'info' | 'success' | 'warning' | 'error';

type StatusBarProps = {
  message: string;
  statusType?: StatusType;
  leftAdornment?: ReactNode;
  badges?: ReactNode[];
};

const STATUS_ICON: Record<StatusType, ReactNode> = {
  info: <Info size={16} />, 
  success: <CheckCircle2 size={16} />, 
  warning: <AlertTriangle size={16} />, 
  error: <OctagonX size={16} />, 
};

export function StatusBar({ message, statusType = 'info', leftAdornment, badges = [] }: StatusBarProps) {
  const icon = STATUS_ICON[statusType] ?? STATUS_ICON.info;

  return (
    <footer className="status-bar" role="status" aria-live="polite">
      <div className="status-bar__message">
        <span aria-hidden="true">{icon}</span>
        {leftAdornment}
        <span>{message}</span>
      </div>
      {badges.length > 0 ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {badges.map((badge, index) => (
            <span key={index} className="status-badge">
              {badge}
            </span>
          ))}
        </div>
      ) : null}
    </footer>
  );
}
