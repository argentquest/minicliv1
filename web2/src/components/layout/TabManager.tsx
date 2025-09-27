import React, { useState } from 'react';
import { Tabs, Button, Space, Tooltip, Dropdown } from 'antd';
import {
  PlusOutlined,
  SaveOutlined,
  CloseOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import type { Tab } from '../../types';

interface TabManagerProps {
  tabs: Tab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onTabSave: (tabId: string) => void;
  onNewTab: () => void;
  onTabsAction?: (action: string, tabId?: string) => void;
}

export const TabManager: React.FC<TabManagerProps> = ({
  tabs,
  activeTabId,
  onTabChange,
  onTabClose,
  onTabSave,
  onNewTab,
  onTabsAction,
}) => {
  const [draggedTab, setDraggedTab] = useState<string | null>(null);

  const handleTabEdit = (targetKey: React.MouseEvent | React.KeyboardEvent | string, action: 'add' | 'remove') => {
    if (action === 'add') {
      onNewTab();
    } else if (action === 'remove' && typeof targetKey === 'string') {
      onTabClose(targetKey);
    }
  };

  const getTabMenuItems = (tab: Tab): MenuProps['items'] => [
    {
      key: 'save',
      label: 'Save Tab',
      icon: <SaveOutlined />,
      onClick: () => onTabSave(tab.id),
    },
    {
      key: 'duplicate',
      label: 'Duplicate Tab',
      onClick: () => onTabsAction?.('duplicate', tab.id),
    },
    {
      type: 'divider',
    },
    {
      key: 'close',
      label: 'Close Tab',
      icon: <CloseOutlined />,
      onClick: () => onTabClose(tab.id),
      danger: true,
    },
    {
      key: 'close-others',
      label: 'Close Other Tabs',
      onClick: () => onTabsAction?.('close-others', tab.id),
    },
    {
      key: 'close-all',
      label: 'Close All Tabs',
      onClick: () => onTabsAction?.('close-all'),
      danger: true,
    },
  ];

  const tabItems = tabs.map((tab) => {
    const isDirty = tab.isDirty;
    
    return {
      key: tab.id,
      label: (
        <div 
          className="flex items-center gap-2 min-w-0"
          draggable
          onDragStart={() => setDraggedTab(tab.id)}
          onDragEnd={() => setDraggedTab(null)}
        >
          <span className="truncate max-w-[120px]">
            {tab.title}
            {isDirty && <span className="text-orange-500">*</span>}
          </span>
          
          <div className="flex items-center gap-1 ml-auto">
            {isDirty && (
              <Tooltip title="Save Tab">
                <Button
                  type="text"
                  size="small"
                  icon={<SaveOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTabSave(tab.id);
                  }}
                  className="!p-0 !w-4 !h-4 !min-w-0 opacity-60 hover:opacity-100"
                />
              </Tooltip>
            )}
            
            <Dropdown
              menu={{ items: getTabMenuItems(tab) }}
              trigger={['click']}
              placement="bottomRight"
            >
              <Button
                type="text"
                size="small"
                icon={<MoreOutlined />}
                onClick={(e) => e.stopPropagation()}
                className="!p-0 !w-4 !h-4 !min-w-0 opacity-60 hover:opacity-100"
              />
            </Dropdown>
            
            {tabs.length > 1 && (
              <Tooltip title="Close Tab">
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTabClose(tab.id);
                  }}
                  className="!p-0 !w-4 !h-4 !min-w-0 opacity-60 hover:opacity-100"
                />
              </Tooltip>
            )}
          </div>
        </div>
      ),
      children: null, // Content will be handled by parent component
    };
  });

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="flex items-center justify-between px-4 py-2">
        <Tabs
          type="editable-card"
          activeKey={activeTabId}
          onChange={onTabChange}
          onEdit={handleTabEdit}
          items={tabItems}
          className="flex-1 !mb-0"
          size="small"
          hideAdd
          tabBarStyle={{ margin: 0 }}
        />
        
        <Space className="ml-4">
          <Tooltip title="New Tab">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={onNewTab}
              size="small"
              className="!bg-blue-600 !border-blue-600"
            >
              New Tab
            </Button>
          </Tooltip>
          
          <Tooltip title="Save Tab">
            <Button
              icon={<SaveOutlined />}
              onClick={() => onTabSave(activeTabId)}
              size="small"
              disabled={!tabs.find(tab => tab.id === activeTabId)?.isDirty}
            >
              Save Tab
            </Button>
          </Tooltip>
          
          <Tooltip title="Close Tab">
            <Button
              icon={<CloseOutlined />}
              onClick={() => onTabClose(activeTabId)}
              size="small"
              disabled={tabs.length <= 1}
              danger
            >
              Close Tab
            </Button>
          </Tooltip>
        </Space>
      </div>
    </div>
  );
};

export default TabManager;