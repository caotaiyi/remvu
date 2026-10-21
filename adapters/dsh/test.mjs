/** Contract tests use the published Cordis/defineTool APIs and a real bundled engine.
 * Minimal service fixtures exercise callbacks; this is not native GUI/model acceptance. */
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { setTimeout as tick } from 'node:timers/promises'
import { Context } from '@deepseek-ai/cordis'
import { createUserMessage } from '@deepseek-ai/dsh-llm'
import * as plugin from './index.js'

const executable = realpathSync(process.argv[2])
const root = realpathSync(mkdtempSync(join(tmpdir(), 'remvu-dsh-contract-')))
const repo = join(root, 'project'); mkdirSync(repo)
const init = spawnSync(executable, ['init', '--repo', repo, '--platform', 'none'], { encoding: 'utf8' })
assert.equal(init.status, 0, init.stdout + init.stderr)
const ctx = new Context(), tools = new Map()
let mode = 'workspace-write', plan = false
ctx.provide('tools', { register: tool => { tools.set(tool.name, tool); return () => tools.delete(tool.name) } })
ctx.provide('workingDirectory', { get: session => session.cwd })
ctx.provide('sandboxPolicy', { resolve: () => ({ mode, workspaceRoot: repo }) })
ctx.provide('sessionProjections', { stateOf: () => ({ active: plan }) })
const offFiber = ctx.plugin(plugin, { executable, project: repo })
await tick(20)
assert.equal(offFiber.state, 2)
const offSession = { id: 'manual-fixture', cwd: repo }
const offSignal = new AbortController().signal
ctx.emit('tools/result', { name: 'bash', arguments: {}, callId: 'off', agent: { session: offSession } }, { isError: false, content: [] })
await ctx.parallel('session/flush', offSession)
const offContext = await ctx.waterfall('agent/pre-step', { agent: { session: offSession }, signal: offSignal }, async () => ({ kind: 'enter', messages: [] }))
assert.equal(offContext.messages.length, 0)
assert.equal(JSON.parse(spawnSync(executable, ['events', '--repo', repo], { encoding: 'utf8' }).stdout).total, 0)
await offFiber.dispose()
const fiber = ctx.plugin(plugin, { executable, project: repo, recording: true })
await tick(20)
assert.equal(fiber.state, 2, 'Plugin must reach real Cordis ACTIVE state')
assert.equal(tools.size, 5)
const session = { id: 'dsh-fixture', cwd: repo }, agent = { session }
const signal = new AbortController().signal
const events = () => JSON.parse(spawnSync(executable, ['events', '--repo', repo], { encoding: 'utf8' }).stdout)
ctx.emit('session/event', session, { type: 'user/message', seq: 1, data: createUserMessage({ content: [{ type: 'text', text: 'Keep full features.' }], source: { kind: 'user' } }) })
ctx.emit('session/event', session, { type: 'assistant/message', seq: 2, data: { stream: [{ reasoning: 'never export this hidden string' }] } })
ctx.emit('tools/result', { name: 'bash', arguments: { command: 'fixture failing check' }, callId: 'one', agent }, { isError: true, content: [{ type: 'text', text: 'fixture failed' }, { type: 'reasoning', text: 'never export this hidden string' }] })
ctx.emit('tools/result', { name: 'remvu_save', arguments: {}, callId: 'self', agent }, { isError: false, content: [] })
await ctx.parallel('session/flush', session)
assert.equal(events().total, 2)
const first = await ctx.waterfall('agent/pre-step', { agent, signal }, async () => ({ kind: 'enter', messages: [] }))
assert.equal(first.messages.length, 1)
const same = await ctx.waterfall('agent/pre-step', { agent, signal }, async () => ({ kind: 'enter', messages: [] }))
assert.equal(same.messages.length, 0, 'Unchanged memory should not be reinjected every step')
assert(first.messages[0].content[0].text.length < 4000)
ctx.emit('tools/result', { name: 'bash', arguments: {}, callId: 'new-observation', agent }, { isError: false, content: [] })
await ctx.parallel('session/flush', session)
const afterEvent = await ctx.waterfall('agent/pre-step', { agent, signal }, async () => ({ kind: 'enter', messages: [] }))
assert.equal(afterEvent.messages.length, 0, 'Ordinary observations must not trigger a new context injection')
ctx.emit('session/event', session, { type: 'compaction/end' })
const afterCompaction = await ctx.waterfall('agent/pre-step', { agent, signal }, async () => ({ kind: 'enter', messages: [] }))
assert.equal(afterCompaction.messages.length, 1)
const resume = JSON.parse(await tools.get('remvu_resume').execute({}, { agent, signal }))
assert.equal(resume.memory.event_count, 3)
const saved = JSON.parse(await tools.get('remvu_save').execute({}, { agent, signal }))
assert.equal(saved.pending_consolidation, true)
const show = JSON.parse(await tools.get('remvu_show').execute({ id: events().events[1].id }, { agent, signal }))
assert.equal(show.event.result, 'failed')
assert(!JSON.stringify(show).includes('never export this hidden string'))
mode = 'read-only'
ctx.emit('tools/result', { name: 'bash', arguments: {}, callId: 'readonly', agent }, { isError: false, content: [] })
await assert.rejects(() => tools.get('remvu_save').execute({}, { agent, signal }), /read-only/)
mode = 'workspace-write'; plan = true
ctx.emit('session/event', session, { type: 'user/message', seq: 3, data: createUserMessage({ content: [{ type: 'text', text: 'Plan only.' }], source: { kind: 'user' } }) })
await assert.rejects(() => tools.get('remvu_save').execute({}, { agent, signal }), /plan/)
plan = false
await ctx.parallel('session/flush', session)
assert.equal(events().total, 3)
const outside = { session: { id: 'other', cwd: root } }
await assert.rejects(() => tools.get('remvu_resume').execute({}, { agent: outside, signal }), /outside/)
ctx.emit('session/event', session, { type: 'compaction/end' })
const statePath = join(repo, '.remvu/state.json')
const originalState = readFileSync(statePath)
writeFileSync(statePath, '{broken')
const warning = await ctx.waterfall('agent/pre-step', { agent, signal }, async () => ({ kind: 'enter', messages: [] }))
const noRetry = await ctx.waterfall('agent/pre-step', { agent, signal }, async () => ({ kind: 'enter', messages: [] }))
assert.equal(warning.messages.length, 1)
assert.equal(noRetry.messages.length, 0, 'A failed memory read must not repeat a warning or retry on every step')
writeFileSync(statePath, originalState)
await fiber.dispose()
assert.equal(fiber.state, 4)
rmSync(root, { recursive: true })
console.log(JSON.stringify({ ok: true, dsh: '0.2.1-rc.2', tests: ['manual_default_no_recording_or_injection', 'one_injection_per_compaction_window', 'real_cordis_lifecycle', 'published_defineTool', 'bundled_transport', 'observable_only', 'self_event_exclusion', 'bounded_context_dedup', 'failed_result_preserved', 'pending_save_truthful', 'read_only_and_plan', 'workspace_isolation', 'disposal'], scope: 'Contract fixtures, not a real model or GUI session.' }))
