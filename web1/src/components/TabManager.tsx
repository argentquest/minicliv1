
import { Plus, Save, X } from 'lucide-react';

import { ActionButton } from './ActionButton';
import { ChatView } from './ChatView';
import type { ChatMessage } from '../types';

type TabDescriptor = {
  id: string;
  title: string;
  dirty: boolean;
  messages: ChatMessage[];
};

type TabManagerProps = {
  tabs: TabDescriptor[];
  activeTabId: string;
  onSelectTab: (tabId: string) => void;
  onNewTab: () => void;
  onCloseTab: (tabId: string) => void;
  onSaveTab: (tabId: string) => void;
};

export function TabManager({
  tabs,
  activeTabId,
  onSelectTab,
  onNewTab,
  onCloseTab,
  onSaveTab,
}: TabManagerProps) {
  const activeTab = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0];
  const canClose = tabs.length > 1 && Boolean(activeTab);

  return (
    <section className="tab-manager" aria-label="Conversation tabs">
      <div className="tab-bar">
        <div className="tab-list" role="tablist" aria-label="Conversations">
          {tabs.map((tab) => {
            const isActive = tab.id === activeTabId;
            const classes = [
              'tab-button',
              isActive ? 'tab-button--active' : '',
              tab.dirty ? 'tab-button--dirty' : '',
            ]
              .filter(Boolean)
              .join(' ');

            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={classes}
                onClick={() => onSelectTab(tab.id)}
              >
                {tab.title}
              </button>
            );
          })}
        </div>

        <div className="tab-controls">
          <ActionButton
            icon={<Plus size={16} />}
            variant="accent"
            onClick={onNewTab}
            aria-label="Create new conversation tab"
          >
            New Tab
          </ActionButton>
          <ActionButton
            icon={<Save size={16} />}
            onClick={() => activeTab && onSaveTab(activeTab.id)}
            disabled={!activeTab}
            aria-label="Save current tab"
          >
            Save Tab
          </ActionButton>
          <ActionButton
            icon={<X size={16} />}
            onClick={() => activeTab && onCloseTab(activeTab.id)}
            disabled={!canClose}
            aria-label="Close current tab"
          >
            Close Tab
          </ActionButton>
        </div>
      </div>

      <ChatView messages={activeTab?.messages ?? []} />
    </section>
  );
}
