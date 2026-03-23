const fs = require('fs');
const http = require('http');
const path = require('path');
const { execSync } = require('child_process');
const next = require('next');

const projectRoot = path.resolve(__dirname, '..');
const lockPath = path.join(projectRoot, '.next', 'dev', 'lock');
const useTurbopack = process.argv.includes('--turbopack');
const host = process.env.HOST || '127.0.0.1';
const port = Number(process.env.PORT || 3000);

process.env.NEXT_LOCAL_WINDOWS_WORKAROUNDS = '1';

function log(msg) {
  process.stdout.write(`[dev-safe] ${msg}\n`);
}

function removeStaleLock() {
  if (!fs.existsSync(lockPath)) {
    return;
  }

  try {
    fs.rmSync(lockPath, { force: true });
    log('Removed stale .next/dev/lock file.');
  } catch (error) {
    log('Another Next.js dev server may still be running (lock is active).');
    log('Stop existing dev server terminals, then run "npm run dev" again.');
    process.exit(0);
  }
}

function getPort3000PidWindows() {
  try {
    const raw = execSync(
      'powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess)"',
      { stdio: ['ignore', 'pipe', 'ignore'] }
    )
      .toString()
      .trim();

    if (!raw) return null;
    const pid = Number(raw);
    return Number.isFinite(pid) ? pid : null;
  } catch {
    return null;
  }
}

function getProcessCommandLineWindows(pid) {
  try {
    const filter = `ProcessId = ${pid}`;
    const raw = execSync(
      `powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter '${filter}' -ErrorAction SilentlyContinue; if ($p) { $p.CommandLine }"`,
      { stdio: ['ignore', 'pipe', 'ignore'] }
    )
      .toString()
      .trim();

    return raw || '';
  } catch {
    return '';
  }
}

function ensurePort3000IsUsable() {
  if (process.platform !== 'win32') return;

  const pid = getPort3000PidWindows();
  if (!pid) return;

  const cmd = getProcessCommandLineWindows(pid).toLowerCase();
  const root = projectRoot.toLowerCase();
  const isLikelyOldNextDev = cmd.includes('next dev') || cmd.includes('dev-safe-start.js');
  const isSameWorkspaceProcess = cmd.includes(root);

  if (isLikelyOldNextDev || isSameWorkspaceProcess) {
    try {
      process.kill(pid, 'SIGTERM');
      log(`Freed port 3000 by stopping stale process ${pid}.`);
    } catch {
      log(`Port 3000 is in use by process ${pid}. Could not auto-stop it.`);
      log('Close that process manually, then run "npm run dev" again.');
      process.exit(1);
    }
    return;
  }

  log(`Port 3000 is in use by process ${pid} (not from this project).`);
  log('Close that process manually if you want this app on http://localhost:3000');
}

async function startNextDev() {
  const app = next({
    dev: true,
    dir: projectRoot,
    hostname: host,
    port,
    turbopack: useTurbopack,
  });

  const handle = app.getRequestHandler();

  await app.prepare();

  const server = http.createServer((req, res) => handle(req, res));

  server.on('error', (error) => {
    console.error(error);
    process.exit(1);
  });

  server.listen(port, host, () => {
    log(`Next.js dev server ready at http://${host}:${port}${useTurbopack ? ' (Turbopack)' : ''}`);
  });
}

removeStaleLock();
ensurePort3000IsUsable();
startNextDev().catch((error) => {
  console.error(error);
  process.exit(1);
});
