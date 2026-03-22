// frontend/src/components/vendor/TaskStatusTabs.tsx
'use client';

import { TaskStatus } from '@/types/vendorTasks';

interface TaskStatusTabsProps {
  activeTab: TaskStatus;
  onChange: (status: TaskStatus) => void;
  counts: {
    pending_response: number;
    assigned: number;
    completed: number;
    rejected_expired: number;
  };
}

type CountKey = 'pending_response' | 'assigned' | 'completed' | 'rejected_expired';

const tabs: Array<{ id: TaskStatus; label: string; countKey: CountKey }> = [
  { id: 'pending_response', label: 'Pending Response', countKey: 'pending_response' },
  { id: 'assigned', label: 'In Progress', countKey: 'assigned' },
  { id: 'completed', label: 'Completed', countKey: 'completed' },
  { id: 'rejected', label: 'Rejected/Expired', countKey: 'rejected_expired' },
];

export function TaskStatusTabs({ activeTab, onChange, counts }: TaskStatusTabsProps) {
  return (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => {
          const count = counts[tab.countKey];
          const isActive = activeTab === tab.id || (tab.id === 'rejected' && activeTab === 'expired');
          
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`
                relative py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${isActive 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="flex items-center gap-2">
                {tab.label}
                {count > 0 && (
                  <span className={`
                    inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${isActive ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}
                  `}>
                    {count}
                  </span>
                )}
              </span>
              {isActive && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full" />
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}