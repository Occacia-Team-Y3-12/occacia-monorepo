const fs = require('fs');
const path = require('path');
const configShared = require('next/dist/server/config-shared');
const { Bundler } = require('next/dist/lib/bundler');

// The default config injects generateBuildId: () => null, which breaks when
// Next sends the merged config through worker threads on this Windows setup.
configShared.defaultConfig.generateBuildId = undefined;
process.env.NEXT_LOCAL_WINDOWS_WORKAROUNDS = '1';

function ensureSafeExportWorkerPatch() {
  const exportIndexPath = require.resolve('next/dist/export/index.js');
  const source = fs.readFileSync(exportIndexPath, 'utf8');
  const needle = '        if (staticWorker) {';

  if (source.includes("process.env.NEXT_BUILD_SAFE_EXPORT_WORKER === '1'")) {
    return;
  }

  const replacement = `        if (process.env.NEXT_BUILD_SAFE_EXPORT_WORKER === '1') {
            const exportWorker = require('./worker');
            let onActivity;
            let onActivityAbort;
            worker = {
                setOnActivity (handler) {
                    onActivity = handler;
                },
                setOnActivityAbort (handler) {
                    onActivityAbort = handler;
                },
                async exportPages (input) {
                    onActivity == null ? void 0 : onActivity();
                    try {
                        return await exportWorker.exportPages(input);
                    } finally{
                        onActivityAbort == null ? void 0 : onActivityAbort();
                    }
                }
            };
        } else if (staticWorker) {`;

  if (!source.includes(needle)) {
    throw new Error(`Could not find export worker hook in ${path.basename(exportIndexPath)}`);
  }

  fs.writeFileSync(exportIndexPath, source.replace(needle, replacement), 'utf8');
}

ensureSafeExportWorkerPatch();

process.env.NEXT_BUILD_SAFE_EXPORT_WORKER = '1';

const build = require('next/dist/build').default;

build(process.cwd(), false, false, false, false, false, false, Bundler.Webpack)
  .then(() => {
    process.exit(0);
  })
  .catch((error) => {
    console.error('');
    console.error('> Build error occurred');
    console.error(error);
    process.exit(1);
  });
