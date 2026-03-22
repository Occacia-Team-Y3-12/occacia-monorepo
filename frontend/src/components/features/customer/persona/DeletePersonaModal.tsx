'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Loader2, X } from 'lucide-react';

type DeletePersonaModalProps = {
  isOpen: boolean;
  isDeleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export function DeletePersonaModal({
  isOpen,
  isDeleting,
  onClose,
  onConfirm,
}: DeletePersonaModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-[#0D47A1]/18 backdrop-blur-sm"
          />

          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-md rounded-3xl border border-[#DCE4F2] bg-white p-6 shadow-[0_24px_60px_-30px_rgba(13,71,161,0.28)]"
            >
              <div className="mb-4 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FFF4F4]">
                    <AlertTriangle className="h-6 w-6 text-[#B23C3C]" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-[#0D47A1]">Delete Persona</h2>
                    <p className="text-sm text-[#5B6780]">This action cannot be undone</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isDeleting}
                  className="text-[#7A87A3] transition hover:text-[#0D47A1]"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <p className="mb-6 text-sm leading-relaxed text-[#5B6780]">
                Are you sure you want to delete this persona? All your preferences and settings will be permanently removed. You'll need to create a new persona to receive personalized recommendations.
              </p>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isDeleting}
                  className="flex-1 rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-4 py-2.5 text-sm font-semibold text-[#4A5976] transition hover:border-[#BFD0EE] hover:bg-[#F1F6FE] disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={onConfirm}
                  disabled={isDeleting}
                  className="flex-1 rounded-full bg-[#B23C3C] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#992D2D] disabled:opacity-50"
                >
                  {isDeleting ? (
                    <span className="inline-flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Deleting...
                    </span>
                  ) : (
                    'Delete Persona'
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
