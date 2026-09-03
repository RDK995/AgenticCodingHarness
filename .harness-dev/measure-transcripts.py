#!/usr/bin/env python3
import json, os, re, glob, sys
from collections import defaultdict

BASE = '/Users/ryankenny/.claude/projects/-Users-ryankenny-Projects-phoneToLocalModel'

PRICES = {  # per Mtok: input, output, cache_read, cache_write
    'opus':  (15.0, 75.0, 1.50, 18.75),
    'sonnet': (3.0, 15.0, 0.30, 3.75),
    'haiku':  (1.0, 5.0, 0.10, 1.25),
}
def model_class(m):
    m = (m or '').lower()
    for k in PRICES:
        if k in m: return k
    return 'opus'  # conservative default

def cost(model, u):
    p = PRICES[model_class(model)]
    return (u.get('input_tokens',0)*p[0] + u.get('output_tokens',0)*p[1] +
            u.get('cache_read_input_tokens',0)*p[2] + u.get('cache_creation_input_tokens',0)*p[3]) / 1e6

LOCATE_BASH = re.compile(r'^\s*(wc|ls|find|sed\s+-n|head|tail|grep|rg|git\s+rev-parse|git\s+status|git\s+log|git\s+branch|cat\s+-n)\b')

def iter_records(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: yield json.loads(line)
            except json.JSONDecodeError: continue

def analyze_file(path):
    """Return per-file stats: deduped usage, turns, tool calls, final text, peak context, user prompts."""
    seen = set()
    models = set()
    usage_sum = defaultdict(int)
    dollars = 0.0
    peak_ctx = 0
    tool_calls = []   # (name, input_json_str)
    texts = []        # assistant text blocks in order
    user_prompts = [] # (timestamp, text) top-level user prompts
    first_ts = last_ts = None
    n_api = 0
    for r in iter_records(path):
        t = r.get('type')
        ts = r.get('timestamp')
        if ts:
            if first_ts is None: first_ts = ts
            last_ts = ts
        if t == 'user':
            c = (r.get('message') or {}).get('content')
            txt = None
            if isinstance(c, str): txt = c
            elif isinstance(c, list):
                parts = [b.get('text','') for b in c if isinstance(b,dict) and b.get('type')=='text']
                if parts: txt = '\n'.join(parts)
            if txt and 'tool_result' not in str(type(c)):
                user_prompts.append((ts, txt))
        if t != 'assistant': continue
        m = r.get('message') or {}
        mid = m.get('id')
        models.add(m.get('model'))
        # tool calls & text: collect from ALL records (content is split across records, same id)
        c = m.get('content')
        if isinstance(c, list):
            for b in c:
                if not isinstance(b, dict): continue
                if b.get('type') == 'tool_use':
                    tool_calls.append((b.get('name'), json.dumps(b.get('input',{}), sort_keys=True)))
                elif b.get('type') == 'text':
                    texts.append(b.get('text',''))
        if mid in seen: continue
        seen.add(mid)
        n_api += 1
        u = m.get('usage') or {}
        ctx = u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0)
        peak_ctx = max(peak_ctx, ctx)
        for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
            usage_sum[k] += u.get(k,0)
        dollars += cost(m.get('model'), u)
    return dict(api_calls=n_api, usage=dict(usage_sum), dollars=dollars, peak_ctx=peak_ctx,
                tool_calls=tool_calls, texts=texts, models=models,
                user_prompts=user_prompts, first_ts=first_ts, last_ts=last_ts)

MILE_RE = re.compile(r'\b(?:P1-)?(M\d+[a-z]?(?:-(?:i|ii|iii|iv|v))?)\b')
def milestones_in(text):
    return set(MILE_RE.findall(text or ''))

sessions = {}
all_models = set()

for jl in sorted(glob.glob(os.path.join(BASE, '*.jsonl'))):
    sid = os.path.basename(jl)[:-6]
    sess = dict(sid=sid, main=analyze_file(jl), agents=[])
    all_models |= sess['main']['models']
    subdir = os.path.join(BASE, sid, 'subagents')
    if os.path.isdir(subdir):
        for aj in sorted(glob.glob(os.path.join(subdir, 'agent-*.jsonl'))):
            aid = os.path.basename(aj)[6:-6]
            meta = {}
            mp = os.path.join(subdir, f'agent-{aid}.meta.json')
            if os.path.exists(mp):
                try: meta = json.load(open(mp))
                except: pass
            st = analyze_file(aj)
            all_models |= st['models']
            st['agentId'] = aid
            st['agentType'] = meta.get('agentType','unknown')
            st['description'] = meta.get('description','')
            st['parentAgentId'] = meta.get('parentAgentId')
            sess['agents'].append(st)
    sessions[sid] = sess

# ---- role bucketing ----
def role_of(agent):
    at = agent['agentType']
    d = (agent['description'] or '').lower()
    if at == 'harness:orchestrator':
        return 'orchestrator-fix' if 'fix' in d else 'orchestrator-impl'
    return {'harness:worker':'worker','harness:verifier':'verifier','harness:reviewer':'reviewer',
            'harness:navigator':'navigator','harness:as-built':'as-built'}.get(at, 'other-agent:'+at)

# ---- milestone per session ----
def session_milestone(sess):
    ms = set()
    for a in sess['agents']:
        if a['agentType'].startswith('harness:orchestrator'):
            ms |= milestones_in(a['description'])
    if not ms:
        for a in sess['agents']:
            ms |= milestones_in(a['description'])
    if not ms:
        for ts, t in sess['main']['user_prompts'][:3]:
            ms |= milestones_in(t)
    return ms

# ---- output ----
out = {}
role_totals = defaultdict(lambda: defaultdict(float))
mile_totals = defaultdict(float)
mile_roles = defaultdict(lambda: defaultdict(float))
session_rows = []
orch_rows = []
nav_rows = []
verifier_rows = []
clear_flags = []
top_ctx = []
top_turns = []
sleep_hits = []
repeat_offenders = []

for sid, sess in sorted(sessions.items(), key=lambda kv: kv[1]['main']['first_ts'] or ''):
    ms = session_milestone(sess)
    mlabel = '+'.join(sorted(ms)) if ms else '(none)'
    total = sess['main']['dollars']
    role_costs = defaultdict(float)
    role_costs['skill-session'] = sess['main']['dollars']
    role_totals['skill-session']['$'] += sess['main']['dollars']
    role_totals['skill-session']['calls'] += sess['main']['api_calls']
    for k,v in sess['main']['usage'].items(): role_totals['skill-session'][k]+=v
    for a in sess['agents']:
        r = role_of(a)
        role_costs[r] += a['dollars']
        total += a['dollars']
        role_totals[r]['$'] += a['dollars']
        role_totals[r]['calls'] += a['api_calls']
        for k,v in a['usage'].items(): role_totals[r][k]+=v
        top_ctx.append((a['peak_ctx'], sid[:8], r, a['description']))
        top_turns.append((a['api_calls'], sid[:8], r, a['description'], a['dollars']))
        # sleep polling
        for name, inp in a['tool_calls']:
            if name=='Bash' and re.search(r'\bsleep\s+\d', inp):
                sleep_hits.append((sid[:8], r, a['description'], inp[:120]))
        # repeat reads (all agents, for offender list)
        cnt = defaultdict(int)
        for tc in a['tool_calls']: cnt[tc]+=1
        rep = sum(v-1 for v in cnt.values() if v>1)
        if a['tool_calls']:
            repeat_offenders.append((rep/len(a['tool_calls']), rep, len(a['tool_calls']), sid[:8], r, a['description']))
        if r == 'verifier':
            verifier_rows.append(dict(sid=sid[:8], desc=a['description'], tools=len(a['tool_calls']),
                                      repeats=rep, pct=100*rep/len(a['tool_calls']) if a['tool_calls'] else 0,
                                      dollars=a['dollars']))
        if r == 'navigator':
            nav_rows.append(dict(sid=sid[:8], desc=a['description'], dollars=a['dollars'],
                                 turns=a['api_calls'], tools=len(a['tool_calls'])))
        if r.startswith('orchestrator'):
            final_text = ''
            for t in reversed(a['texts']):
                if t.strip(): final_text = t; break
            has_continue = bool(re.search(r'\bCONTINUE\b', final_text)) or any('CONTINUE' in t for t in a['texts'][-3:])
            # navigation classification
            loc = 0
            for name, inp in a['tool_calls']:
                if name in ('Read','Glob','Grep'): loc += 1
                elif name=='Bash':
                    try: cmd = json.loads(inp).get('command','')
                    except: cmd = ''
                    if LOCATE_BASH.match(cmd): loc += 1
            orch_rows.append(dict(sid=sid[:8], mile=mlabel, desc=a['description'], phase=r,
                                  turns=a['api_calls'], peak_ctx=a['peak_ctx'],
                                  continue_=has_continue, dollars=a['dollars'],
                                  tools=len(a['tool_calls']), locate=loc,
                                  final_snippet=final_text[-200:] if final_text else ''))
    top_ctx.append((sess['main']['peak_ctx'], sid[:8], 'skill-session', mlabel))
    top_turns.append((sess['main']['api_calls'], sid[:8], 'skill-session', mlabel, sess['main']['dollars']))
    # /clear check: milestones mentioned across ALL user prompts of the main session
    prompt_ms = set()
    for ts, t in sess['main']['user_prompts']:
        if t.startswith('<'): continue
        prompt_ms |= milestones_in(t)
    if len(prompt_ms) > 1:
        clear_flags.append((sid[:8], sorted(prompt_ms)))
    for m in (ms or {'(none)'}):
        share = total/len(ms) if ms else total
        mile_totals[m if ms else '(none)'] += share
        for r,v in role_costs.items():
            mile_roles[m if ms else '(none)'][r] += v/len(ms) if ms else v
    session_rows.append(dict(sid=sid[:8], mile=mlabel, first=sess['main']['first_ts'],
                             total=total, main=sess['main']['dollars'],
                             agents=len(sess['agents'])))

print('=== MODELS SEEN ===')
print(sorted(m for m in all_models if m))
print()
print('=== PER-SESSION (chronological) ===')
print(f"{'session':9} {'first_ts':21} {'milestone':16} {'agents':>6} {'main$':>8} {'total$':>8}")
for r in session_rows:
    print(f"{r['sid']:9} {(r['first'] or '')[:19]:21} {r['mile'][:16]:16} {r['agents']:6d} {r['main']:8.2f} {r['total']:8.2f}")
print()
print('=== ROLE TOTALS (deduped) ===')
print(f"{'role':20} {'calls':>6} {'input':>10} {'output':>10} {'cache_rd':>12} {'cache_wr':>12} {'$':>9}")
for role in sorted(role_totals, key=lambda r: -role_totals[r]['$']):
    d = role_totals[role]
    print(f"{role:20} {int(d['calls']):6d} {int(d['input_tokens']):10d} {int(d['output_tokens']):10d} {int(d['cache_read_input_tokens']):12d} {int(d['cache_creation_input_tokens']):12d} {d['$']:9.2f}")
print(f"TOTAL $ {sum(d['$'] for d in role_totals.values()):.2f}")
print()
print('=== MILESTONE COSTS ===')
for m in sorted(mile_totals, key=lambda x: -mile_totals[x]):
    roles = mile_roles[m]
    coord = sum(v for k,v in roles.items() if k in ('skill-session','orchestrator-impl','orchestrator-fix','navigator','as-built','reviewer','verifier'))
    print(f"{m:10} ${mile_totals[m]:8.2f}   roles: " + ', '.join(f"{k}=${v:.2f}" for k,v in sorted(roles.items(), key=lambda kv:-kv[1]) if v>0.005))
print()
print('=== ORCHESTRATOR INVOCATIONS (turn budget) ===')
print(f"{'sid':9} {'milestone':12} {'phase':17} {'turns':>5} {'peakCtx':>8} {'CONT':>5} {'tools':>5} {'locate':>6} {'loc%':>5} {'$':>7}  desc")
for r in orch_rows:
    pct = 100*r['locate']/r['tools'] if r['tools'] else 0
    print(f"{r['sid']:9} {r['mile'][:12]:12} {r['phase']:17} {r['turns']:5d} {r['peak_ctx']:8d} {str(r['continue_']):>5} {r['tools']:5d} {r['locate']:6d} {pct:5.0f} {r['dollars']:7.2f}  {r['desc'][:45]}")
print()
print('=== NAVIGATOR INVOCATIONS ===')
for r in nav_rows:
    print(f"{r['sid']:9} turns={r['turns']:3d} tools={r['tools']:3d} ${r['dollars']:.3f}  {r['desc'][:60]}")
print(f"navigator count={len(nav_rows)} total ${sum(r['dollars'] for r in nav_rows):.2f}")
print()
print('=== VERIFIER EXACT-REPEAT TOOL CALLS ===')
for r in sorted(verifier_rows, key=lambda x:-x['pct'])[:15]:
    print(f"{r['sid']:9} tools={r['tools']:3d} repeats={r['repeats']:3d} ({r['pct']:.0f}%) ${r['dollars']:.2f}  {r['desc'][:50]}")
vt = sum(r['tools'] for r in verifier_rows); vr = sum(r['repeats'] for r in verifier_rows)
print(f"ALL verifiers: {vr}/{vt} = {100*vr/vt if vt else 0:.1f}% exact repeats across {len(verifier_rows)} verifier runs")
print()
print('=== /clear FLAGS (sessions whose prompts span multiple milestones) ===')
for sid, ms in clear_flags: print(sid, ms)
print('(none)' if not clear_flags else '')
print()
print('=== WASTE: TOP 5 PEAK CONTEXTS ===')
for c in sorted(top_ctx, reverse=True)[:5]: print(c)
print('=== WASTE: TOP 5 LONGEST INVOCATIONS (turns) ===')
for c in sorted(top_turns, reverse=True)[:5]: print(c)
print('=== WASTE: TOP REPEAT OFFENDERS (any role, min 20 tool calls) ===')
for frac, rep, tot, sid, role, desc in sorted([x for x in repeat_offenders if x[2]>=20], reverse=True)[:8]:
    print(f"{sid} {role:16} {rep}/{tot} = {100*frac:.0f}%  {desc[:50]}")
print('=== WASTE: SLEEP-POLLING BASH CALLS ===')
print(f"count={len(sleep_hits)}")
for h in sleep_hits[:10]: print(h)
