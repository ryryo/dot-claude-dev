#!/usr/bin/env python3
"""Emit MCP auth headers from macOS Keychain; never log the credential."""

import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', default='codex-devin-mcp')
    parser.add_argument('--account', default='devin')
    parser.add_argument('--org-id', help='Required only for PAT/enterprise keys')
    parser.add_argument('--check', action='store_true', help='Report availability without headers')
    args = parser.parse_args()
    try:
        result = subprocess.run(
            ['/usr/bin/security', 'find-generic-password', '-s', args.service,
             '-a', args.account, '-w'],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        print('Devin MCP Keychain lookup failed.', file=sys.stderr)
        return 1
    token = result.stdout.strip()
    if result.returncode or not token.startswith('cog_') or any(c.isspace() for c in token):
        print('Devin MCP credential is unavailable or unsupported.', file=sys.stderr)
        return 1
    if args.check:
        print(json.dumps({'credential_available': True}))
    else:
        headers = {'Authorization': f'Bearer {token}'}
        if args.org_id:
            headers['X-Org-Id'] = args.org_id
        print(json.dumps(headers))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
