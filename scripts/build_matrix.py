"""Build a safe GitHub Actions matrix from a comma-separated model list."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys


def build_matrix(raw: str) -> dict:
    models = []
    seen = set()
    for item in raw.split(','):
        model = item.strip()
        if not model or model in seen:
            continue
        seen.add(model)
        slug = re.sub(r'[^A-Za-z0-9_.-]+', '_', model).strip('._-') or 'model'
        # Add a short digest so different tags that sanitize to the same slug cannot collide.
        safe_name = f"{slug[:48]}-{hashlib.sha256(model.encode()).hexdigest()[:8]}"
        models.append({"model": model, "safe_name": safe_name})
    if not models:
        raise ValueError('At least one non-empty model tag is required.')
    return {"include": models}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', required=True)
    parser.add_argument('--output', help='GitHub Actions GITHUB_OUTPUT path')
    args = parser.parse_args()
    matrix = build_matrix(args.models)
    encoded = json.dumps(matrix, separators=(',', ':'))
    if args.output:
        with open(args.output, 'a', encoding='utf-8') as stream:
            stream.write(f'matrix={encoded}\n')
            stream.write('models=' + json.dumps([x['model'] for x in matrix['include']], separators=(',', ':')) + '\n')
    print(encoded)
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
