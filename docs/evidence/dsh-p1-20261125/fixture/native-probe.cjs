const fs = require('node:fs')
const path = require('node:path')
const { execFileSync, spawnSync } = require('node:child_process')
const { DatabaseSync } = require('node:sqlite')

const workspace = process.env.DSH_P1_WORKSPACE
const forbidden = process.env.DSH_P1_FORBIDDEN
const results = {}

async function check(name, fn) {
  try {
    results[name] = { ok: true, detail: await fn() }
  } catch (error) {
    results[name] = {
      ok: false,
      code: error && error.code,
      message: error && error.message,
    }
  }
}

async function main() {
  await check('identity', () => ({
    uid: process.getuid(),
    gid: process.getgid(),
    home: process.env.HOME,
    dshHome: process.env.DSH_HOME,
    node: process.version,
    arch: process.arch,
  }))

  await check('workspace-write', () => {
    const target = path.join(workspace, 'native-probe.txt')
    fs.writeFileSync(target, 'workspace-ok\n', { mode: 0o600 })
    const value = fs.readFileSync(target, 'utf8').trim()
    fs.unlinkSync(target)
    return value
  })

  await check('forbidden-read-denied', () => {
    try {
      fs.readFileSync(path.join(forbidden, 'root-only-marker'))
      throw new Error('unexpectedly readable')
    } catch (error) {
      if (error && (error.code === 'EACCES' || error.code === 'EPERM')) return error.code
      throw error
    }
  })

  await check('shadow-read-denied', () => {
    try {
      fs.readFileSync('/etc/shadow')
      throw new Error('unexpectedly readable')
    } catch (error) {
      if (error && (error.code === 'EACCES' || error.code === 'EPERM')) return error.code
      throw error
    }
  })

  await check('etc-write-denied', () => {
    const target = '/etc/dsh-p1-should-not-exist'
    try {
      fs.writeFileSync(target, 'unexpected\n')
      throw new Error('unexpectedly writable')
    } catch (error) {
      if (error && (error.code === 'EACCES' || error.code === 'EPERM')) return error.code
      throw error
    }
  })

  await check('sqlite', () => {
    const db = new DatabaseSync(':memory:')
    const row = db.prepare('select 40 + 2 as answer').get()
    db.close()
    return row.answer
  })

  await check('sharp', async () => {
    const sharp = require('sharp')
    const buffer = await sharp({
      create: { width: 2, height: 2, channels: 4, background: '#336699ff' },
    }).png().toBuffer()
    return { bytes: buffer.length, versions: sharp.versions }
  })

  await check('koffi', () => {
    const koffi = require('koffi')
    return koffi.version || 'loaded'
  })

  await check('ripgrep', () => {
    const { rgPath } = require('@vscode/ripgrep')
    return execFileSync(rgPath, ['--version'], { encoding: 'utf8' }).split('\n')[0]
  })

  await check('shell', () => execFileSync('/bin/sh', ['-c', 'printf shell-ok'], {
    encoding: 'utf8',
  }))

  await check('git', () => execFileSync('git', ['--version'], { encoding: 'utf8' }).trim())

  await check('flock-addon', async () => {
    const { tryLockExclusive } = await import('@deepseek-ai/node-addon-system/flock')
    const lockPath = path.join(workspace, 'native-probe.lock')
    const fd = fs.openSync(lockPath, 'w', 0o600)
    try {
      await tryLockExclusive(fd)
      return 'locked'
    } finally {
      fs.closeSync(fd)
      fs.unlinkSync(lockPath)
    }
  })

  await check('landlock', async () => {
    const addon = await import('@deepseek-ai/node-addon-system/landlock-run')
    return { path: addon.launcherPath(), enforcement: addon.probe(undefined, { timeoutMs: 3000 }) }
  })

  await check('bubblewrap-probe', () => {
    const probe = spawnSync('bwrap', [
      '--ro-bind', '/', '/', '--dev', '/dev', '--unshare-pid', '--proc', '/proc',
      '--die-with-parent', '--', 'true',
    ], { encoding: 'utf8', timeout: 5000 })
    return {
      usable: probe.status === 0,
      status: probe.status,
      errorCode: probe.error && probe.error.code,
      stderr: probe.stderr && probe.stderr.trim(),
    }
  })

  await check('node-pty', () => new Promise((resolve, reject) => {
    const pty = require('node-pty')
    let output = ''
    const terminal = pty.spawn('/bin/sh', ['-c', 'printf pty-ok'], {
      name: 'xterm-256color',
      cols: 80,
      rows: 24,
      cwd: workspace,
      env: process.env,
    })
    const timer = setTimeout(() => {
      terminal.kill()
      reject(new Error('PTY probe timed out'))
    }, 5000)
    terminal.onData((data) => { output += data })
    terminal.onExit(({ exitCode }) => {
      clearTimeout(timer)
      if (exitCode !== 0) reject(new Error(`PTY exited ${exitCode}`))
      else resolve(output)
    })
  }))

  await check('dsh-subprocess-local-load', async () => {
    const module = await import('@deepseek-ai/dsh-subprocess-local')
    return Object.keys(module).sort()
  })

  console.log(JSON.stringify(results, null, 2))
  if (Object.values(results).some((entry) => !entry.ok)) process.exitCode = 1
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
