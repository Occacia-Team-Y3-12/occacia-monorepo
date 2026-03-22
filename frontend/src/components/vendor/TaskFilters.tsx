'use client';

import { TaskPriority } from '@/types/vendorTasks';
import { Search, X } from 'lucide-react';
import { useState } from 'react';

interface TaskFiltersProps {
  filters: {
    search?: string;
    priority?: TaskPriority;
  };
  onChange: (filters: { search?: string; priority?: TaskPriority }) => void;
}

export function TaskFilters({ filters, onChange }: TaskFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '');

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    onChange({ ...filters, search: value || undefined });
  };

  const handlePriorityChange = (priority: TaskPriority | undefined) => {
    onChange({ ...filters, priority });
  };

  const handleClearAll = () => {
    setSearchInput('');
    onChange({ search: undefined, priority: undefined });
  };

  const hasActiveFilters = searchInput || filters.priority;

  return (
    <div className="flex flex-col gap-4 mb-6">
      <div className="flex flex-col md:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search tasks by title or customer name..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
        </div>

        {/* Priority Filter */}
        <select
          className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={filters.priority || ''}
          onChange={(e) => handlePriorityChange((e.target.value as TaskPriority) || undefined)}
          aria-label="Filter tasks by priority"
        >
          <option value="">All Priorities</option>
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>

        {/* Clear Button */}
        {hasActiveFilters && (
          <button
            onClick={handleClearAll}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <X className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
