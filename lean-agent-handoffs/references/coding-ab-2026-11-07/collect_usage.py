#!/usr/bin/env python3
"""Collect a strict, non-content usage whitelist for one local coding arm."""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re


RUN_DIR = Path(__file__).resolve().parent
SESSION_DIR = Path.home() / '.codex/sessions/2026/11/07'
SKILL_PATH = str(Path.home() / '.agents/skills/lean-agent-handoffs/SKILL.md')
COUNTERS = {
    'input': 'input_tokens',
    'cached_input': 'cached_input_tokens',
    'output': 'output_tokens',
    'reasoning_output': 'reasoning_output_tokens',
    'total': 'total_tokens',
}


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def records(path):
    with path.open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def usage(source):
    result = {label: source[key] for label, key in COUNTERS.items()}
    if any(type(value) is not int or value < 0 for value in result.values()):
        raise ValueError('Native counters must be nonnegative integers')
    if result['total'] != result['input'] + result['output']:
        raise ValueError('Native total is not input plus output')
    if result['cached_input'] > result['input']:
        raise ValueError('Native cached input exceeds input')
    if result['reasoning_output'] > result['output']:
        raise ValueError('Native reasoning output exceeds output')
    return result


def add_usage(items):
    result = {label: sum(item[label] for item in items) for label in COUNTERS}
    usage({COUNTERS[label]: value for label, value in result.items()})
    return result


def metadata_index():
    index = {}
    for path in sorted(SESSION_DIR.glob('*.jsonl')):
        # Only the first session_meta is examined for unrelated sessions. A
        # forked log may later contain copied parent session_meta records.
        first = next(records(path), None)
        if not first or first.get('type') != 'session_meta':
            continue
        payload = first.get('payload', {})
        source = payload.get('source')
        parent = None
        if isinstance(source, dict):
            parent = (source.get('subagent', {}).get('thread_spawn', {})
                      .get('parent_thread_id'))
        thread_id = payload.get('id')
        if thread_id:
            index[thread_id] = {
                'path': path,
                'created_at': payload['timestamp'],
                'parent_thread_id': parent,
            }
    return index


def own_turns(log, created_at, ancestor_turn_ids):
    cutoff = timestamp(created_at)
    return {
        item['payload']['turn_id']
        for item in log
        if item.get('type') == 'event_msg'
        and item.get('payload', {}).get('type') == 'task_started'
        and item['payload'].get('turn_id')
        and item['payload']['turn_id'] not in ancestor_turn_ids
        and timestamp(item['timestamp']) >= cutoff
    }


def inspect_session(thread_id, meta, ancestor_turn_ids):
    # Only matched root/descendant logs reach this function.
    log = list(records(meta['path']))
    turn_ids = own_turns(log, meta['created_at'], ancestor_turn_ids)
    if not turn_ids:
        raise ValueError('Matched session has no new task_started turn')
    active_turn = None
    latest_count = None
    token_count_events = 0
    requests = {}
    models = set()
    tools = Counter()
    calls = {}
    outputs = {}
    spawn_audit = []
    completed_turn_ids = set()
    for position, item in enumerate(log):
        kind = item.get('type')
        payload = item.get('payload', {})
        subtype = payload.get('type')
        if kind == 'event_msg' and subtype == 'task_started':
            active_turn = payload.get('turn_id')
        if kind == 'event_msg' and subtype == 'task_complete':
            if payload.get('turn_id') in turn_ids:
                completed_turn_ids.add(payload['turn_id'])
        if kind == 'turn_context' and payload.get('turn_id') in turn_ids:
            models.add((payload.get('model'),
                        payload.get('effort', payload.get('reasoning_effort'))))
        if kind == 'token_usage_record' and payload.get('turn_id') in turn_ids:
            if payload.get('thread_id') != thread_id:
                raise ValueError('Own usage record has a different thread ID')
            key = payload.get('response_id') or ('record', position)
            entry = usage(payload['usage'])
            if key in requests and requests[key] != entry:
                raise ValueError('Conflicting duplicate native request usage')
            requests[key] = entry
        if (kind == 'event_msg' and subtype == 'token_count'
                and active_turn in turn_ids):
            info = payload.get('info') or {}
            if info.get('total_token_usage'):
                latest_count = (item['timestamp'], usage(info['total_token_usage']))
                token_count_events += 1
        if kind != 'response_item':
            continue
        if subtype in ('function_call_output', 'custom_tool_call_output'):
            outputs[payload.get('call_id')] = payload.get('output')
            continue
        if subtype not in ('function_call', 'custom_tool_call'):
            continue
        native_meta = payload.get('internal_chat_message_metadata_passthrough') or {}
        # Event timestamps in replayed history are rewritten at fork creation.
        # Native turn IDs exclude those inherited calls, even after the cutoff.
        if native_meta.get('turn_id') not in turn_ids:
            continue
        created = native_meta.get('create_time')
        if created is not None and created < timestamp(meta['created_at']).timestamp():
            raise ValueError('Own tool call predates session creation')
        name = payload.get('name')
        namespace = payload.get('namespace')
        label = f'{namespace}.{name}' if namespace else name
        tools[label] += 1
        call_id = payload.get('call_id')
        calls[call_id] = payload
        if name == 'spawn_agent':
            arguments = json.loads(payload.get('arguments') or '{}')
            explicit = 'fork_turns' in arguments
            spawn_audit.append({
                'fork_turns': arguments.get('fork_turns', 'all'),
                'parameter_status': 'explicit' if explicit else 'omitted_default_all',
            })
    if latest_count is None or not requests:
        raise ValueError('Matched session lacks native usage counters or requests')
    request_sum = add_usage(list(requests.values()))
    if request_sum != latest_count[1]:
        raise ValueError('Native request sum differs from final cumulative token_count')
    skill_reads = 0
    for call_id, call in calls.items():
        arguments = call.get('arguments', call.get('input', ''))
        output = json.dumps(outputs.get(call_id), ensure_ascii=False)
        if (SKILL_PATH in arguments and '# Lean Agent Handoffs' in output
                and any(reader in arguments for reader in
                        ('cat ', 'read_text', 'sed ', 'open('))):
            skill_reads += 1
    return {
        'thread_id': thread_id,
        'parent_thread_id': meta['parent_thread_id'],
        'created_at': meta['created_at'],
        'usage': latest_count[1],
        'token_count_timestamp': latest_count[0],
        'token_count_event_count': token_count_events,
        'model_request_count': len(requests),
        'models_and_efforts': [
            {'model': model, 'effort': effort}
            for model, effort in sorted(models, key=str)
        ],
        'own_turn_count': len(turn_ids),
        'all_own_turns_completed': completed_turn_ids == turn_ids,
        'tool_call_audit': {
            'own_call_count': sum(tools.values()),
            'counts_by_tool': dict(sorted(tools.items())),
            'skill_entry_read_evidence': {'path': SKILL_PATH, 'count': skill_reads},
            'spawn_calls': spawn_audit,
        },
    }, turn_ids


def main():
    global RUN_DIR, SESSION_DIR, SKILL_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ARM_NAME')
    parser.add_argument('--run-dir', type=Path, default=RUN_DIR)
    parser.add_argument('--session-dir', type=Path, default=SESSION_DIR)
    parser.add_argument('--skill-path', default=SKILL_PATH)
    args = parser.parse_args()
    RUN_DIR, SESSION_DIR, SKILL_PATH = args.run_dir, args.session_dir, args.skill_path
    arm = args.ARM_NAME
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', arm):
        parser.error('ARM_NAME must be a simple arm filename label')
    starts = [item['thread_id'] for item in records(RUN_DIR / f'{arm}.events.jsonl')
              if item.get('type') == 'thread.started']
    if len(starts) != 1:
        raise ValueError('Arm events must contain exactly one thread.started')
    root_id = starts[0]
    index = metadata_index()
    if root_id not in index:
        raise ValueError('Coordinator metadata not found in the allowed session date')
    family = [root_id]
    for parent_id in family:
        family.extend(sorted(thread_id for thread_id, meta in index.items()
                             if meta['parent_thread_id'] == parent_id
                             and thread_id not in family))
    sessions = []
    turns_by_thread = {}
    for thread_id in family:
        ancestor_turn_ids = set()
        ancestor = index[thread_id]['parent_thread_id']
        while ancestor in turns_by_thread:
            ancestor_turn_ids.update(turns_by_thread[ancestor])
            ancestor = index[ancestor]['parent_thread_id']
        session, turns_by_thread[thread_id] = inspect_session(
            thread_id, index[thread_id], ancestor_turn_ids)
        session['role'] = 'coordinator' if thread_id == root_id else 'descendant'
        session['child_count'] = sum(index[other]['parent_thread_id'] == thread_id
                                     for other in family)
        sessions.append(session)
    aggregate = add_usage([session['usage'] for session in sessions])
    result = {
        'schema_version': 1,
        'arm': arm,
        'coordinator_thread_id': root_id,
        'source': 'local_native_token_count_and_token_usage_record',
        'model_request_count_source': 'unique_native_token_usage_record_response_ids',
        'scope': 'coordinator_plus_all_descendants',
        'child_count': sessions[0]['child_count'],
        'descendant_count': len(sessions) - 1,
        'usage': aggregate,
        'model_request_count': sum(s['model_request_count'] for s in sessions),
        'sessions': sessions,
        'validation': {
            'total_equals_input_plus_output': True,
            'cached_input_subset_of_input': True,
            'reasoning_output_subset_of_output': True,
            'per_request_sum_equals_session_cumulative': True,
            'inherited_tool_calls_excluded_by_ancestor_and_native_turn_ids': True,
            'exactly_one_child_and_no_grandchildren': len(sessions) == 2
                and sessions[0]['child_count'] == 1,
            'all_own_turns_completed': all(s['all_own_turns_completed'] for s in sessions),
        },
    }
    destination = RUN_DIR / f'{arm}.usage.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'path': str(destination), 'usage': aggregate,
                      'model_request_count': result['model_request_count'],
                      'validation': result['validation']}))


if __name__ == '__main__':
    main()
