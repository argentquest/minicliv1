import React from 'react';
import { Modal as AntModal, Button } from 'antd';
import { CloseOutlined } from '@ant-design/icons';

interface ModalProps {
  title: string;
  open: boolean;
  onCancel: () => void;
  onOk?: () => void;
  children: React.ReactNode;
  width?: number | string;
  footer?: React.ReactNode | null;
  okText?: string;
  cancelText?: string;
  confirmLoading?: boolean;
  destroyOnClose?: boolean;
  maskClosable?: boolean;
  centered?: boolean;
  className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  title,
  open,
  onCancel,
  onOk,
  children,
  width = 520,
  footer,
  okText = 'OK',
  cancelText = 'Cancel',
  confirmLoading = false,
  destroyOnClose = true,
  maskClosable = true,
  centered = true,
  className = '',
}) => {
  const defaultFooter = footer === null ? null : footer || (
    <div className="flex justify-end gap-2">
      <Button onClick={onCancel}>{cancelText}</Button>
      {onOk && (
        <Button 
          type="primary" 
          onClick={onOk}
          loading={confirmLoading}
        >
          {okText}
        </Button>
      )}
    </div>
  );

  return (
    <AntModal
      title={
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold">{title}</span>
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={onCancel}
            className="!p-1"
          />
        </div>
      }
      open={open}
      onCancel={onCancel}
      footer={defaultFooter}
      width={width}
      destroyOnHidden={destroyOnClose}
      maskClosable={maskClosable}
      centered={centered}
      className={`whispercode-modal ${className}`}
      closable={false} // We handle close button in custom title
    >
      <div className="py-4">
        {children}
      </div>
    </AntModal>
  );
};

export default Modal;