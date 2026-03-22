'use client';

import { motion } from 'framer-motion';
import { Loader2, RotateCcw, Save, Trash2 } from 'lucide-react';

type PersonaEditFooterProps = {
  isDirty: boolean;
  isSaving: boolean;
  onSave: () => void;
  onReset: () => void;
  onDelete: () => void;
};

export function PersonaEditFooter({
  isDirty,
  isSaving,
  onSave,
  onReset,
  onDelete,
}: PersonaEditFooterProps) {
  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-[#0d1117]/95 backdrop-blur-lg"
    >
      <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6">
        {isDirty && (
          <div className="mb-3 text-center text-xs text-[#f5c871]">
            You have unsaved changes
          </div>
        )}
        
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={onDelete}
            disabled={isSaving}
            className="inline-flex items-center gap-2 rounded-full border border-[#ff9d9d]/20 bg-[#ff9d9d]/10 px-4 py-2 text-sm font-semibold text-[#ffd0d0] transition hover:bg-[#ff9d9d]/20 disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
            Delete Persona
          </button>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onReset}
              disabled={!isDirty || isSaving}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white/80 transition hover:bg-white/10 disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </button>

            <button
              type="button"
              onClick={onSave}
              disabled={isSaving}
              className="inline-flex items-center gap-2 rounded-full bg-[#f5c871] px-6 py-2 text-sm font-semibold text-[#0a0d14] transition hover:bg-[#ffe2a2] disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </motion.footer>
  );
}
