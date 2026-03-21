'use client';

import React, { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { TaskDetails, VendorShortlist } from '@/types/customer/task';

interface ModifyTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: TaskDetails;
  onReassign: (vendorId: string) => Promise<void>;
  onRemove: () => Promise<void>;
}

const ModifyTaskModal: React.FC<ModifyTaskModalProps> = ({
  isOpen,
  onClose,
  task,
  onReassign,
  onRemove,
}) => {
  const [selectedVendor, setSelectedVendor] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [action, setAction] = useState<'replace' | 'remove' | null>(null);

  const handleReassign = async () => {
    if (!selectedVendor) return;
    setIsLoading(true);
    try {
      await onReassign(selectedVendor);
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemove = async () => {
    setIsLoading(true);
    try {
      await onRemove();
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Modify Rejected Task" size="lg">
      <div className="space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="font-semibold text-red-900">{task.serviceType}</h3>
          <p className="text-sm text-red-700 mt-1">Vendor: {task.vendorName}</p>
          {task.rejectionReason && (
            <p className="text-sm text-red-600 mt-2">
              <span className="font-medium">Reason:</span> {task.rejectionReason}
            </p>
          )}
        </div>

        {!action && (
          <div className="space-y-3">
            <p className="text-gray-700">Choose an action:</p>
            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={() => setAction('replace')}
                className="flex-1"
              >
                Replace Vendor
              </Button>
              <Button
                variant="danger"
                onClick={() => setAction('remove')}
                className="flex-1"
              >
                Remove Task
              </Button>
            </div>
          </div>
        )}

        {action === 'replace' && (
          <div className="space-y-3">
            <h4 className="font-semibold text-gray-900">Select a New Vendor</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {task.recommendedVendors.map((vendor: VendorShortlist) => (
                <label
                  key={vendor.vendorId}
                  className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition ${
                    selectedVendor === vendor.vendorId
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="vendor"
                    value={vendor.vendorId}
                    checked={selectedVendor === vendor.vendorId}
                    onChange={(e) => setSelectedVendor(e.target.value)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{vendor.vendorName}</p>
                    <p className="text-sm text-gray-600">
                      Rating: {vendor.rating} ⭐ | ${vendor.price}
                    </p>
                  </div>
                </label>
              ))}
            </div>
            <div className="flex gap-3 pt-3">
              <Button
                variant="ghost"
                onClick={() => setAction(null)}
                disabled={isLoading}
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={handleReassign}
                disabled={!selectedVendor || isLoading}
                isLoading={isLoading}
                className="flex-1"
              >
                Confirm Replacement
              </Button>
            </div>
          </div>
        )}

        {action === 'remove' && (
          <div className="space-y-3">
            <p className="text-gray-700">
              Are you sure you want to remove this task from the event? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <Button
                variant="ghost"
                onClick={() => setAction(null)}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleRemove}
                isLoading={isLoading}
                className="flex-1"
              >
                Confirm Removal
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default ModifyTaskModal;
