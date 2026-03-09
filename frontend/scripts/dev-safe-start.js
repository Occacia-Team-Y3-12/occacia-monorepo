const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { execSync } = require('child_process');

const projectRoot = path.resolve(__dirname, '..');
const lockPath = path.join(projectRoot, '.next', 'dev', 'lock');

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

function startNextDev() {
  const isWindows = process.platform === 'win32';
  const command = isWindows ? 'npm run dev:raw' : 'npm';
  const args = isWindows ? [] : ['run', 'dev:raw'];

  const child = spawn(command, args, {
    cwd: projectRoot,
    stdio: 'inherit',
    shell: isWindows,
  });

  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 0);
  });
}

removeStaleLock();
ensurePort3000IsUsable();
startNextDev();
