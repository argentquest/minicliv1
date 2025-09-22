import React, { useState, useEffect, type ChangeEvent } from 'react';
import { Loader2, RefreshCcw, FolderOpen } from 'lucide-react';

import { ActionButton } from '../ActionButton';
import type { CodebaseFile, TopFoldersResponse } from '../../types';
import { Modal } from './Modal';
import { getTopFolders } from '../../api';

interface FolderOption {
  value: string;
  label: string;
}

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
  const [topFolders, setTopFolders] = useState<FolderOption[]>([]);
  const [isLoadingFolders, setIsLoadingFolders] = useState(false);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (isOpen) {
      const codePath = import.meta.env.VITE_CODE_PATH || 'C:/Code2025/minicli';
      const rootBasename = codePath.split('/').pop() || 'root';
      if (!directory) {
        onDirectoryChange(codePath);
      }
      loadTopFolders();
    }
  }, [isOpen]);

  const loadTopFolders = async () => {
    if (!isOpen) return;
    setIsLoadingFolders(true);
    try {
      const response: TopFoldersResponse = await getTopFolders();
      const codePath = import.meta.env.VITE_CODE_PATH || 'C:/Code2025/minicli'; // Fallback if not set
      const rootBasename = codePath.split('/').pop() || 'root';
      const options: FolderOption[] = [
        { value: rootBasename, label: 'Root (All Files)' },
        ...response.folders.map(folder => ({
          value: folder,
          label: folder
        }))
      ];
      setTopFolders(options);
    } catch (err) {
      console.error('Failed to load top folders:', err);
      const codePath = import.meta.env.VITE_CODE_PATH || 'C:/Code2025/minicli';
      const rootBasename = codePath.split('/').pop() || 'root';
      setTopFolders([{ value: rootBasename, label: 'Root (All Files)' }]);
    } finally {
      setIsLoadingFolders(false);
    }
  };

  const handleFolderSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = event.target.value;
    const codePath = import.meta.env.VITE_CODE_PATH || 'C:/Code2025/minicli';
    const rootBasename = codePath.split('/').pop() || 'root';
    if (selectedValue === rootBasename) {
      onDirectoryChange(codePath);
    } else if (selectedValue) {
      onDirectoryChange(`${codePath}/${selectedValue}`);
    } else {
      onDirectoryChange(codePath);
    }
    // Load directory after selection
    onLoadDirectory();
  };

  const handleDirectoryChange = (event: ChangeEvent<HTMLInputElement>) => {
    onDirectoryChange(event.target.value);
  };


  const footer = (
    <>
      <ActionButton onClick={onClose} disabled={isLoading || isLoadingFolders}>
        Cancel
      </ActionButton>
      <ActionButton
        variant="primary"
        onClick={onApply}
        disabled={isLoading || isLoadingFolders || selectedFiles.length === 0}
      >
        Apply Context
      </ActionButton>
    </>
  );

  const selectAll = () => {
    filteredFiles.forEach((file) => {
      const value = file.relativePath || file.path;
      if (!selectedFiles.includes(value)) {
        onToggleFile(value);
      }
    });
  };

  const selectNone = () => {
    selectedFiles.forEach((value) => {
      // Since onToggleFile toggles, call for all selected to deselect
      onToggleFile(value);
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredFiles = files.filter((file) => {
    const path = (file.relativePath || file.path).toLowerCase();
    return path.includes(filter.toLowerCase());
  });

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
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
        <div className="file-selection-buttons">
          <button onClick={selectAll} disabled={isLoading} className="btn btn-secondary">
            Select All ({filteredFiles.length})
          </button>
          <button onClick={selectNone} disabled={isLoading} className="btn btn-secondary">
            Select None
          </button>
        </div>
        <div style={{ marginBottom: '8px' }}>
          <label htmlFor="file-filter" style={{ display: 'block', marginBottom: '4px', fontSize: '14px' }}>
            Filter files:
          </label>
          <input
            id="file-filter"
            type="text"
            placeholder="Filter files..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ width: '100%', padding: '4px 8px', border: '1px solid var(--border-color)', borderRadius: '4px' }}
            disabled={isLoading}
          />
        </div>
        <div className="context-file-list single-column" style={{
          flex: 1,
          overflowY: 'auto',
          minHeight: 0,
          display: 'grid',
          gridTemplateColumns: 'auto 1fr auto',
          gap: '8px',
          alignItems: 'center',
          fontSize: '14px'
        }}>
          {/* Header */}
          <div style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}></div>
          <div style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>File Path</div>
          <div style={{ fontWeight: 'bold', color: 'var(--text-primary)', textAlign: 'right' }}>Size</div>
          {filteredFiles
            .slice()
            .sort((a, b) => {
              const pathA = a.relativePath || a.path;
              const pathB = b.relativePath || b.path;
              return pathA.localeCompare(pathB);
            })
            .map((file) => {
              const value = file.relativePath || file.path;
              const isChecked = selectedFiles.includes(value);
              return (
                <>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    disabled={isLoading}
                    onChange={() => onToggleFile(value)}
                    style={{ margin: 0 }}
                  />
                  <label
                    key={value}
                    className={isChecked ? 'context-file--selected' : ''}
                    style={{
                      width: '100%',
                      display: 'block',
                      margin: 0,
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      padding: '4px 0'
                    }}
                    onClick={() => !isLoading && onToggleFile(value)}
                  >
                    <span>{value}</span>
                  </label>
                  <small style={{ color: 'var(--text-secondary)', textAlign: 'right' }}>
                    {formatFileSize(file.size)}
                  </small>
                </>
              );
            })}
        </div>
      </div>
    );
  };

  return (
    <Modal title="Conversation Context" isOpen={isOpen} onClose={onClose} footer={footer} width="900px" height="80vh">
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
        {(isLoading || isLoadingFolders) && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(255, 255, 255, 0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10,
            }}
          >
            <Loader2 size={48} className="spin" />
            <div style={{ marginTop: '8px', fontSize: '14px' }}>
              {isLoading ? 'Retrieving files...' : 'Loading folders...'}
            </div>
          </div>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div className="form-group">
            <label htmlFor="context-directory">Select Folder</label>
            <div className="modal-actions-inline">
              <select
                id="context-directory"
                value={directory ? directory.split('/').pop() || topFolders[0]?.value || '' : topFolders[0]?.value || ''}
                onChange={handleFolderSelect}
                disabled={isLoading}
                style={{ flex: 1, minWidth: 0 }}
              >
                {topFolders.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <ActionButton
                icon={isLoading ? <Loader2 size={16} className="spin" /> : <RefreshCcw size={16} />}
                onClick={onLoadDirectory}
                disabled={isLoading || !directory}
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
              disabled={isLoading || isLoadingFolders}
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
        </div>
      </div>
    </Modal>
  );
}
