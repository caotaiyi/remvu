#!/usr/bin/env python3
"""Paired native trials: ordinary HANDOFF.md versus Markdown Remvu (no runtime).

This developer evaluation uses Python and Node. The installed Remvu workflow
never does. Native calls use existing subscriptions. No hidden reasoning saved.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import run_live as live

ROOT = Path(__file__).resolve().parents[1]
TASKS = Path(__file__).with_name('markdown-tasks.json')


def verify(repo, task):
    # Fixed cases stay outside the receiver's workspace; no prompt-dependent judge.
    script = '''const f=require(process.argv[1]); let raw=''; process.stdin.on('data',x=>raw+=x); process.stdin.on('end',()=>{const cases=JSON.parse(raw); const results=cases.map(([input,want],i)=>{const before=JSON.stringify(input);try {const actual=f(input);return {case:i,passed:JSON.stringify(actual)===JSON.stringify(want)&&before===JSON.stringify(input)};}catch(e){return {case:i,passed:false};}}); console.log(JSON.stringify(results));});'''
    try:
        p = subprocess.run(['node', '-e', script, str(repo / 'app.cjs')], input=json.dumps(task['cases']),
                           capture_output=True, text=True, timeout=10)
        checks = json.loads(p.stdout) if p.returncode == 0 else []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        checks = []
    return {'passed': sum(c['passed'] for c in checks), 'total': len(task['cases']),
            'failed_case_ids': [i for i in range(len(task['cases'])) if not any(c['case'] == i and c['passed'] for c in checks)]}


def call(platform, binary, repo, prompt, out):
    # Reuse allowlisting and usage accounting; no raw provider logs on disk.
    old = live.native_command
    def command(agent, executable, project):
        args = old(agent, executable, project)
        if agent == 'claude':
            args[args.index('--allowedTools') + 1] = 'Read,Edit,Write,Bash(git *),Bash(node *),Bash(ls*),Bash(cat*)'
        return args
    # Avoid mutating the imported function in concurrent workers.
    cmd = command(platform, binary, repo)
    started = time.monotonic()
    try:
        process = subprocess.run(cmd, cwd=repo, input=prompt, capture_output=True, text=True,
                                 timeout=240, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        result = live.filter_native_output(process.stdout, process.stderr)
        result.update(returncode=process.returncode, timed_out=False)
    except subprocess.TimeoutExpired:
        result = {'returncode': None, 'timed_out': True, 'reported_usage': [], 'visible_records': []}
    result.update(elapsed_seconds=round(time.monotonic()-started,3), prompt_chars=len(prompt), platform=platform)
    live.write_json(out, result)
    return result


def fixture(path, initial):
    path.mkdir(parents=True)
    (path/'app.cjs').write_text(initial)
    live.git(path, 'init', '-q')
    live.git(path, 'config', 'user.name', 'Remvu fixture')
    live.git(path, 'config', 'user.email', 'fixture@example.invalid')
    live.git(path, 'add', 'app.cjs')
    live.git(path, 'commit', '-qm', 'Accepted starting implementation')


def trial(task, index, binaries, out):
    folder = out/task['id']
    producer = folder/'producer'
    fixture(producer, task['initial'])
    platform = 'claude' if index % 2 == 0 else 'codex'
    receiver = 'codex' if platform == 'claude' else 'claude'
    starting = verify(producer, task)
    prompt = ('This is a synthetic project handoff test. Do not change app.cjs. '
              'The following are explicit user requirements for this project:\n'+json.dumps({k:task[k] for k in ('goal','next','constraints','rejected')})+
              '\nThe evaluator actually checked the starting file: '+json.dumps(starting)+
              '. These are outstanding checks, not passing checks. First write an ordinary concise HANDOFF.md of the kind you would normally give another coding agent, including what it needs to continue. '
              'Then read '+str(ROOT/'skills/remvu/SKILL.md')+' and use its Markdown save workflow to write .remvu/notes/REMVU.md, with no Python, Remvu runtime or hooks. '
              'Use only project Git/file operations needed for the save. Preserve the original code. Stop after reading back both handoffs.')
    production = call(platform,binaries[platform],producer,prompt,folder/'producer-result.json')
    ordinary = producer/'HANDOFF.md'
    note = producer/'.remvu/notes/REMVU.md'
    record = {'task':task['id'],'direction':platform+'-'+receiver,'starting_checks':starting,
              'producer_seconds':production['elapsed_seconds'],'producer_returncode':production['returncode'],
              'producer_usage_joint_two_documents':production.get('reported_usage',[]),'arms':[]}
    if not ordinary.is_file() or not note.is_file() or (producer/'app.cjs').read_text()!=task['initial']:
        record['setup_failed']=True
        live.write_json(folder/'summary.json',record)
        return record
    # Alternate arm order to reduce systematic cache/time ordering effects.
    arms = ['handoff','remvu'] if index % 2 == 0 else ['remvu','handoff']
    for arm in arms:
        repo = folder/arm
        fixture(repo,task['initial'])
        source = ordinary if arm=='handoff' else note
        # Both arms have exactly one Markdown file, identical name and next-task prompt.
        (repo/'HANDOFF.md').write_bytes(source.read_bytes())
        prompt = ('Continue this local JavaScript project. Read HANDOFF.md as project evidence. '
                  'Implement this next feature in app.cjs: '+task['next']+
                  ' Preserve the existing public function API and other intended behavior. You may use node for checks. '
                  'Do not install Remvu, invoke Python, access the producer workspace or read unrelated chats. '
                  'Complete the implementation and summarize checks honestly.')
        first = call(receiver,binaries[receiver],repo,prompt,folder/(arm+'-first.json'))
        before_repair = verify(repo,task)
        rounds, elapsed, usage = 0, first['elapsed_seconds'], [first.get('reported_usage',[])]
        last_returncode = first['returncode']
        timed_out = first['timed_out']
        final = before_repair
        if first['returncode']==0 and final['passed']!=final['total']:
            rounds=1
            failures=[{'input':task['cases'][i][0],'expected':task['cases'][i][1]} for i in final['failed_case_ids']]
            correction=call(receiver,binaries[receiver],repo,'Continue the task. Independent fixed checks failed: '+json.dumps(failures)+'. Fix these without regressing the existing contract. Do not install or run Remvu or Python.',folder/(arm+'-repair.json'))
            elapsed+=correction['elapsed_seconds'];usage.append(correction.get('reported_usage',[]))
            last_returncode = correction['returncode']
            timed_out = timed_out or correction['timed_out']
            final=verify(repo,task)
        record['arms'].append({'arm':arm,'handoff_bytes':source.stat().st_size,'initial_returncode':first['returncode'],
                               'initial_checks':before_repair,'final_checks':final,'repair_rounds':rounds,
                               'receiver_seconds':round(elapsed,3),'reported_usage':usage,
                               'last_returncode':last_returncode,'timed_out':timed_out,
                               'completed':last_returncode==0 and not timed_out and final['passed']==final['total']})
        live.write_json(folder/'summary.json',record)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codex',type=Path,required=True);p.add_argument('--claude',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int,default=10)
    p.add_argument('--workers',type=int,choices=(1,2),default=1)
    args=p.parse_args()
    if args.out.exists(): p.error('Use a fresh private output directory')
    if not 1 <= args.limit <= 10: p.error('--limit must be 1..10')
    tasks=json.loads(TASKS.read_text())[:args.limit]
    args.out.mkdir(parents=True,mode=0o700)
    report={'protocol':'markdown-paired/1','task_manifest_sha256':hashlib.sha256(TASKS.read_bytes()).hexdigest(),
            'skill_sha256':hashlib.sha256((ROOT/'skills/remvu/SKILL.md').read_bytes()).hexdigest(),
            'notes_rules_sha256':hashlib.sha256((ROOT/'skills/remvu/references/notes.md').read_bytes()).hexdigest(),
            'template_sha256':hashlib.sha256((ROOT/'skills/remvu/assets/note-template.md').read_bytes()).hexdigest(),
            'clients':{a:live.client_version(b) for a,b in [('codex',args.codex),('claude',args.claude)]},
            'limitations':['Synthetic small JavaScript tasks, not representative of all projects.',
                           'One producer writes both summaries; setup usage cannot isolate Remvu save cost.',
                           'One trial per condition; no statistical reliability or cost-saving claim.',
                           'Ordinary HANDOFF.md is the baseline; no runtime on either receiver.',
                           'Repair rounds count independent evaluator feedback, not all internal rework.',
                           'Rejected-route attempts are not automatically measured; final code needs separate review.',
                           'CLI results do not establish desktop, VS Code or Windows support.',
                           'Client-selected model IDs may differ between invocations; report native model counters without cross-provider token sums.'], 'results':[]}
    live.write_json(args.out/'report.json',report)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(trial,t,i,{'codex':args.codex,'claude':args.claude},args.out):t['id'] for i,t in enumerate(tasks)}
        for future in as_completed(futures):
            try: result=future.result()
            except Exception as exc: result={'task':futures[future],'setup_failed':True,'error_type':type(exc).__name__}
            report['results'].append(result)
            live.write_json(args.out/'report.json',report)
            print(json.dumps({'finished':len(report['results']),'total':len(tasks),'task':result['task'],
                              'setup_failed':result.get('setup_failed',False)},ensure_ascii=False),flush=True)
    return 0 if all(not r.get('setup_failed') for r in report['results']) else 1

if __name__=='__main__': raise SystemExit(main())
