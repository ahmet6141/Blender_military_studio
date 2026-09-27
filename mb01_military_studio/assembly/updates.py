# SPDX-License-Identifier: MIT
"""Deterministic review-only update planner. Does not apply writes or delete assets."""
from .contracts import canonical_hash


def index(records):
    out={}
    for record in records:
        if not isinstance(record,dict) or not record.get('id') or not record.get('owner'):
            raise ValueError('Record needs id and owner')
        if record['id'] in out:raise ValueError('Duplicate component id: '+record['id'])
        for key in ('geometry','material','transform'):
            if key not in record:raise ValueError('Missing fingerprint domain: '+key)
        canonical_hash(record)
        out[record['id']]=record
    return out


def plan_update(old_records,new_records):
    old=index(old_records);new=index(new_records);actions=[]
    for identity in sorted(set(old)|set(new)):
        before,after=old.get(identity),new.get(identity)
        if before is None:action='CREATE';domains=['geometry','material','transform']
        elif after is None:action='KEEP_ORPHAN';domains=[]
        else:
            if before['owner']!=after['owner']:raise ValueError('Owner mismatch: '+identity)
            domains=[k for k in ('geometry','material','transform') if before[k]!=after[k]]
            action='UNCHANGED' if not domains else ('CONFLICT_LOCKED' if before.get('locked') else 'UPDATE')
        actions.append(dict(id=identity,action=action,domains=domains))
    return dict(schema='base01.update_plan/1',dry_run=True,actions=actions,
        requires_review=any(a['action'] in ('KEEP_ORPHAN','CONFLICT_LOCKED') for a in actions),
        performs_writes=False,automatic_deletion=False)
