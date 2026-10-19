/** Reproducible real DSH installation/profile boot. Never sends a model prompt. */
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const [dshArg, appArg, reportArg] = process.argv.slice(2)
const dsh = realpathSync(dshArg), executable = realpathSync(appArg)
const root = realpathSync(mkdtempSync(join(tmpdir(), 'remvu-dsh-host-'))), project = join(root, 'project')
mkdirSync(project)
const env = { ...process.env, DSH_HOME: join(root, 'home'), REMVU_EXECUTABLE: executable, REMVU_PROJECT: project }
function command(bin, args) {
  const p = spawnSync(bin, args, { env, encoding: 'utf8', timeout: 120000 })
  assert.equal(p.status, 0, 'DSH fixture setup failed: ' + (p.stderr || p.stdout).slice(0, 1000))
  return p.stdout
}
command(executable, ['init', '--repo', project, '--platform', 'none'])
command(dsh, ['--profile', 'remvu-smoke', '--from-default-profile', 'sdk', '--dump-config'])
command(dsh, ['plugin', '--profile', 'remvu-smoke', 'add', repoRoot])
const dumped = command(dsh, ['--profile', 'remvu-smoke', '--dump-config'])
assert(dumped.includes('dsh-remvu'))
const resultFile = join(root, 'host-result.json'), probe = join(root, 'probe.mjs'), patch = join(root, 'probe.patch.yml')
writeFileSync(probe, `import {writeFileSync} from 'node:fs';\nexport const name='remvu-probe';export const inject=['remvu','tools'];\nexport function apply(ctx){const tools=['remvu_save','remvu_resume','remvu_check','remvu_events','remvu_show'].filter(n=>!!ctx.tools.get(n));writeFileSync(${JSON.stringify(resultFile)},JSON.stringify({ok:tools.length===5,version:ctx.remvu.version,tools}));console.error('REMVU_HOST_READY');}\n`)
writeFileSync(patch, JSON.stringify([{ insert: [{ id: 'remvu-test-probe', name: probe }] }]))
await new Promise((done, fail) => {
  const child = spawn(dsh, ['--profile', 'remvu-smoke', '--patch', patch], { env, stdio: ['pipe', 'pipe', 'pipe'] })
  let ready = false, error = ''
  child.stdout.resume()
  child.stderr.setEncoding('utf8')
  child.stderr.on('data', d => {
    error += d
    if (!ready && error.includes('REMVU_HOST_READY')) {
      ready = true
      child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'shutdown' }) + '\n')
    }
  })
  child.on('error', fail)
  const timer = setTimeout(() => { child.kill(); fail(new Error('DSH host did not report plugin readiness.')) }, 30000)
  child.on('close', code => { clearTimeout(timer); code === 0 && ready ? done() : fail(new Error('DSH profile boot failed before plugin readiness.')) })
})
const result = JSON.parse(readFileSync(resultFile, 'utf8'))
assert(result.ok)
const report = { ...result, dsh: '0.2.1-rc.2', platform: process.platform, checks: ['official_plugin_add', 'dump_config_layer', 'actual_sdk_profile_boot', 'five_registered_tools', 'clean_shutdown'], model_requests: 0, scope: 'Real host boot without a model request; not GUI or model handoff acceptance.' }
if (reportArg) writeFileSync(reportArg, JSON.stringify(report, null, 2) + '\n')
console.log(JSON.stringify(report))
