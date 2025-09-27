import React, { useState, useEffect } from 'react';
import { Select, Button, Checkbox, Input, Space, Tree, Typography, Spin, message } from 'antd';
import {
  ReloadOutlined,
  FolderOutlined,
  FileOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { Modal } from '../common/Modal';
import type { FileItem } from '../../types';
import ApiService from '../../services/api';

const { Option } = Select;
const { Search } = Input;
const { Text } = Typography;

interface ContextModalProps {
  open: boolean;
  onCancel: () => void;
  onApply: (selectedFiles: FileItem[]) => void;
  initialFiles?: FileItem[];
}

export const ContextModal: React.FC<ContextModalProps> = ({
  open,
  onCancel,
  onApply,
  initialFiles = [],
}) => {
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [currentDirectory, setCurrentDirectory] = useState('Root (All Files)');
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);

  // Initialize selected files from props
  useEffect(() => {
    if (initialFiles.length > 0) {
      setSelectedFiles(new Set(initialFiles.map(f => f.path)));
    }
  }, [initialFiles]);

  // Load files when modal opens
  useEffect(() => {
    if (open) {
      loadFiles();
    }
  }, [open]);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getFiles();
      if (response.success && response.data) {
        setFiles(response.data);
      } else {
        message.error(response.error || 'Failed to load files');
      }
    } catch (error) {
      message.error('Error loading files');
      console.error('Error loading files:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDirectory = async (path: string) => {
    setLoading(true);
    try {
      const response = await ApiService.loadDirectory(path);
      if (response.success && response.data) {
        setFiles(response.data);
        setCurrentDirectory(path);
        message.success('Directory loaded successfully');
      } else {
        message.error(response.error || 'Failed to load directory');
      }
    } catch (error) {
      message.error('Error loading directory');
      console.error('Error loading directory:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    file.path.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleFileToggle = (filePath: string, checked: boolean) => {
    const newSelected = new Set(selectedFiles);
    if (checked) {
      newSelected.add(filePath);
    } else {
      newSelected.delete(filePath);
    }
    setSelectedFiles(newSelected);
  };

  const handleSelectAll = () => {
    const allFilePaths = filteredFiles.map(f => f.path);
    setSelectedFiles(new Set([...selectedFiles, ...allFilePaths]));
  };

  const handleSelectNone = () => {
    setSelectedFiles(new Set());
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const getFileIcon = (file: FileItem) => {
    return file.type === 'directory' ? (
      <FolderOutlined className="text-blue-500" />
    ) : (
      <FileOutlined className="text-gray-500" />
    );
  };

  const handleApply = () => {
    const selectedFileItems = files.filter(file => selectedFiles.has(file.path));
    onApply(selectedFileItems);
    onCancel();
  };

  const directoryOptions = [
    'Root (All Files)',
    'src/',
    'components/',
    'services/',
    'types/',
    'utils/',
  ];

  return (
    <Modal
      title="Conversation Context"
      open={open}
      onCancel={onCancel}
      onOk={handleApply}
      width={800}
      okText="Apply Context"
      cancelText="Cancel"
    >
      <div className="space-y-4">
        {/* Directory Selection */}
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Text className="block mb-2 text-sm font-medium">Select Folder</Text>
            <Select
              value={currentDirectory}
              onChange={setCurrentDirectory}
              className="w-full"
              placeholder="Choose directory"
            >
              {directoryOptions.map(dir => (
                <Option key={dir} value={dir}>{dir}</Option>
              ))}
            </Select>
          </div>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={loadFiles}
            loading={loading}
            className="mt-6"
          >
            Load Directory
          </Button>
        </div>

        {/* File Selection Controls */}
        <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Checkbox
              indeterminate={selectedFiles.size > 0 && selectedFiles.size < filteredFiles.length}
              checked={filteredFiles.length > 0 && selectedFiles.size === filteredFiles.length}
              onChange={(e) => e.target.checked ? handleSelectAll() : handleSelectNone()}
            >
              Persist selected files across questions
            </Checkbox>
          </div>
          
          <Text className="text-sm text-gray-600">
            Directory scanned successfully
          </Text>
        </div>

        {/* File Actions */}
        <div className="flex items-center justify-between">
          <Space>
            <Button
              onClick={handleSelectAll}
              size="small"
              disabled={filteredFiles.length === 0}
            >
              Select All ({filteredFiles.length})
            </Button>
            <Button
              onClick={handleSelectNone}
              size="small"
              disabled={selectedFiles.size === 0}
            >
              Select None
            </Button>
          </Space>

          <Search
            placeholder="Filter files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
            size="small"
          />
        </div>

        {/* File List */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
          <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-12 gap-4 text-xs font-medium text-gray-600 dark:text-gray-400">
              <div className="col-span-7">File Path</div>
              <div className="col-span-3">Size</div>
              <div className="col-span-2 text-right">Actions</div>
            </div>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Spin size="large" />
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No files found
              </div>
            ) : (
              filteredFiles.map((file) => (
                <div
                  key={file.path}
                  className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-gray-100 dark:border-gray-800 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <div className="col-span-7 flex items-center gap-2">
                    <Checkbox
                      checked={selectedFiles.has(file.path)}
                      onChange={(e) => handleFileToggle(file.path, e.target.checked)}
                    />
                    {getFileIcon(file)}
                    <Text className="text-sm truncate">{file.path}</Text>
                  </div>
                  
                  <div className="col-span-3 flex items-center">
                    <Text className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </Text>
                  </div>
                  
                  <div className="col-span-2 flex justify-end">
                    {/* Could add file-specific actions here */}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Selection Summary */}
        <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
          <Text className="text-sm">
            <strong>{selectedFiles.size}</strong> files selected
            {selectedFiles.size > 0 && (
              <span className="text-gray-600 dark:text-gray-400 ml-2">
                Total size: {formatFileSize(
                  files
                    .filter(f => selectedFiles.has(f.path))
                    .reduce((sum, f) => sum + f.size, 0)
                )}
              </span>
            )}
          </Text>
        </div>
      </div>
    </Modal>
  );
};

export default ContextModal;