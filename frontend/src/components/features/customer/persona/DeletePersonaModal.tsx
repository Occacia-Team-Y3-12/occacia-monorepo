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
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />

          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-md rounded-3xl border border-white/10 bg-[#0d1117] p-6 shadow-2xl"
            >
              <div className="mb-4 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#ff9d9d]/10">
                    <AlertTriangle className="h-6 w-6 text-[#ff9d9d]" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Delete Persona</h2>
                    <p className="text-sm text-white/60">This action cannot be undone</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isDeleting}
                  className="text-white/60 transition hover:text-white/90"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <p className="mb-6 text-sm leading-relaxed text-white/70">
                Are you sure you want to delete this persona? All your preferences and settings will be permanently removed. You'll need to create a new persona to receive personalized recommendations.
              </p>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isDeleting}
                  className="flex-1 rounded-full border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white/80 transition hover:bg-white/10 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={onConfirm}
                  disabled={isDeleting}
                  className="flex-1 rounded-full bg-[#ff9d9d] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#ff8080] disabled:opacity-50"
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
