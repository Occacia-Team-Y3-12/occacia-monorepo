const { spawn } = require('child_process');

if (process.platform === 'win32') {
  require('./build-safe-start');
  return;
}

const child = spawn(
  process.execPath,
  [require.resolve('next/dist/bin/next'), 'build', '--webpack'],
  {
    stdio: 'inherit',
    env: process.env,
  }
);

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 0);
});

child.on('error', (error) => {
  console.error(error);
  process.exit(1);
});
