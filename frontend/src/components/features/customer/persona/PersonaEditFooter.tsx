'use client';

import { motion } from 'framer-motion';
import { Loader2, RotateCcw, Save, Trash2 } from 'lucide-react';

type PersonaEditFooterProps = {
  isDirty: boolean;
  isSaving: boolean;
  onSave: () => void;
  onReset: () => void;
  onDelete?: () => void;
  saveLabel?: string;
};

export function PersonaEditFooter({
  isDirty,
  isSaving,
  onSave,
  onReset,
  onDelete,
  saveLabel = 'Save Changes',
}: PersonaEditFooterProps) {
  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#DCE4F2] bg-white/95 backdrop-blur-lg"
    >
      <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6">
        {isDirty && (
          <div className="mb-3 text-center text-xs text-[#0D47A1]">
            You have unsaved changes
          </div>
        )}
        
        <div className="flex flex-wrap items-center justify-between gap-3">
          {onDelete ? (
            <button
              type="button"
              onClick={onDelete}
              disabled={isSaving}
              className="inline-flex items-center gap-2 rounded-full border border-[#F4CDCD] bg-[#FFF4F4] px-4 py-2 text-sm font-semibold text-[#B23C3C] transition hover:bg-[#FFEAEA] disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              Delete Persona
            </button>
          ) : (
            <div />
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onReset}
              disabled={!isDirty || isSaving}
              className="inline-flex items-center gap-2 rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-4 py-2 text-sm font-semibold text-[#4A5976] transition hover:border-[#BFD0EE] hover:bg-[#F1F6FE] disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </button>

            <button
              type="button"
              onClick={onSave}
              disabled={isSaving}
              className="inline-flex items-center gap-2 rounded-full bg-[#0D47A1] px-6 py-2 text-sm font-semibold text-white transition hover:bg-[#4285F4] disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  {saveLabel}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </motion.footer>
  );
}
