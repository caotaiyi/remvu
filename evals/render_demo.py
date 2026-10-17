#!/usr/bin/env python3
"""Render a 30-second replay of published native trial evidence.

Development-only dependency: Pillow. This is a labelled evidence replay, not
an original client screen recording. No model calls or private logs are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import textwrap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=Path('evals/results/live-2026-10-17.json'))
    parser.add_argument('--out', type=Path, default=Path('docs/assets/remvu-live-replay.gif'))
    parser.add_argument('--font', type=Path, help='Optional TrueType font path')
    args = parser.parse_args()
    from PIL import Image, ImageDraw, ImageFont
    report = json.loads(args.report.read_text(encoding='utf-8'))
    trials = {item['direction']: item for item in report['directions']}
    csv = trials['claude-codex']; money = trials['codex-claude']
    if not all(item['acceptance_passed'] for item in (csv, money)):
        raise SystemExit('Both recorded handoffs must pass before rendering this demo.')
    font_path = args.font
    if font_path is None:
        font_path = next((p for p in (
            Path('/System/Library/Fonts/SFNSMono.ttf'),
            Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'),
            Path('C:/Windows/Fonts/consola.ttf'),
        ) if p.is_file()), None)
    def font(size):
        return ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default(size=size)
    width, height = 1200, 720
    bg, fg, quiet, accent = '#F5F2EA', '#202926', '#56625D', '#166B55'
    body_font, small_font = font(24), font(17)
    def frame(number, title, paragraphs):
        canvas = Image.new('RGB', (width, height), bg)
        draw = ImageDraw.Draw(canvas)
        draw.text((58, 36), 'REMVU  /  REAL HANDOFF REPLAY', fill=accent, font=font(22))
        draw.text((58, 90), title, fill=fg, font=font(37))
        y = 165
        for text, emphasized in paragraphs:
            chosen = font(26) if emphasized else body_font
            for line in textwrap.wrap(text, width=70, replace_whitespace=False) or ['']:
                draw.text((58, y), line, fill=accent if emphasized else fg, font=chosen)
                y += 36
            y += 21
        if y > 625:
            raise ValueError('Replay slide overflows; shorten the selected evidence.')
        draw.line((58, 632, 1142, 632), fill='#CFD7CE', width=2)
        draw.text((58, 650), 'Evidence replay, not original screen recording.  |  Actual timings shown.', fill=quiet, font=small_font)
        draw.text((58, 679), 'Source: evals/results/live-2026-10-17.json', fill=quiet, font=small_font)
        draw.text((1080, 679), str(number) + '/6', fill=accent, font=small_font)
        return canvas
    c = csv['arms']['with_memory']; m = money['arms']['with_memory']
    frames = [
        frame(1, 'Claude Code -> Codex', [
            ('Recorded native clients: Claude Code ' + report['clients']['claude']['version'] + ' / Codex ' + report['clients']['codex']['version'], False),
            ('Task: normalize CSV tags without changing their meaning.', True),
            ('Keep case, duplicate tags, order and the public function signature. Use the standard library. Regex and lowercasing were rejected.', False),
            ('Producer finished quoted CSV support. Initial BOM handling was deliberately left open; the real regression failed.', False),
            ('Real producer runtime: ' + str(csv['producer']['elapsed_seconds']) + ' seconds; waiting is compressed.', False),
        ]),
        frame(2, 'One file carries the unfinished task', [
            ('Public artifact: REMVU.md (' + str(csv['handoff']['memory_chars']) + ' characters)', True),
            ('It records user-confirmed constraints, rejected directions, a failed CSV_BOM check and the remaining BOM fix.', False),
            ('Frozen source code: ' + csv['handoff']['source_code_commit'][:12], False),
            ('Private .remvu/ state, original chat and Remvu installation are absent from the fresh receiver.', False),
        ]),
        frame(3, 'A fresh Codex continues from the file', [
            ('Receiver inputs: tags.py + .gitignore + REMVU.md; code Git history is available.', True),
            ('Actual visible final excerpt:', False),
            (c['visible_final_excerpt'].split(' Wrote ')[0].replace('`', ''), False),
            ('Real native elapsed time: ' + str(c['process']['elapsed_seconds']) + ' seconds. The replay compresses the wait.', False),
        ]),
        frame(4, 'Check the result and the retained intent', [
            ('CSV code checks: ' + str(c['code']['passed']) + '/' + str(c['code']['total']) + ' passed', True),
            ('Quoted commas, case and duplicates, empty fields, and the initial BOM case all pass independent checks.', False),
            ('Recall: ' + str(c['recall']['matched_groups']) + '/' + str(c['recall']['total_groups']) + ' fixed term groups matched before editing.', True),
            ('The public report includes stage-1 code, completed code, the standalone memory and both recall files.', False),
        ]),
        frame(5, 'The reverse handoff also passed', [
            ('Codex -> Claude Code: exact integer cents', True),
            ('Decimal + ROUND_HALF_UP stayed intact. Claude added parenthesized negative amounts: (12.345) -> -1235.', False),
            ('Code checks: ' + str(m['code']['passed']) + '/' + str(m['code']['total']) + '. Recall: ' + str(m['recall']['matched_groups']) + '/' + str(m['recall']['total_groups']) + ' term groups.', True),
            ('Real runtimes: producer ' + str(money['producer']['elapsed_seconds']) + 's; receiver ' + str(m['process']['elapsed_seconds']) + 's.', False),
        ]),
        frame(6, 'Read the controls with the results', [
            ('Code-only controls could not identify the unfinished user task. Both wrote needs_context=true and stopped.', False),
            ('With memory, both fresh receivers completed the intended step.', True),
            ('Two fixed cases; lexical recall is not proof of general understanding. Native token counters are published.', False),
            ('No token-saving percentage is claimed: stopping and completing a task use different amounts of work.', False),
        ]),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(args.out, save_all=True, append_images=frames[1:], duration=5000, loop=0, optimize=True)
    manifest = {'artifact': args.out.as_posix(), 'source_report': args.report.as_posix(),
                'source_sha256': hashlib.sha256(args.report.read_bytes()).hexdigest(),
                'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                'frames': 6, 'duration_ms': 30000,
                'presentation': 'Labelled replay of real native evidence, not an original screen recording.'}
    args.out.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
