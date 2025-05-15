#!/usr/bin/env python

"""
Just a dummy module to try stuff with omnibenchmark.
Useful for debugging; i.e. to make modules return arbitrary failures, sleep, etc.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

def parse_gnu_style_args(argv: List[str] = None) -> Dict[str, Optional[str]]:
    """
    Parse command line arguments in GNU style (--flag value) format.
    
    Args:
        argv: List of command line arguments (defaults to sys.argv[1:])
    
    Returns:
        Dictionary of parsed arguments where keys are flag names (without -- prefix)
        and values are the argument values. Flags without values are set to None.
    
    Example:
        Input: ['--name', 'John', '--verbose', '--age', '30']
        Output: {'name': 'John', 'verbose': None, 'age': '30'}
    """
    if argv is None:
        argv = sys.argv[1:]
    
    args = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('--'):
            flag = arg[2:]
            if i + 1 < len(argv) and not argv[i+1].startswith('--'):
                args[flag] = argv[i+1]
                i += 2
            else:
                args[flag] = None
                i += 1
        else:
            # Handle non-flag arguments if needed
            i += 1
    return args

def handle_args(**kwargs):
    fail = kwargs.get('fail', None)
    if fail is not None:
        raise RuntimeError('failing hard')

    out = kwargs.get('output', None)
    if out is not None:
        parent = Path(out).parent
        os.makedirs(parent, exist_ok=True)
        with open(out, 'w') as out_f:
            out_f.write("A" * 32)

    ok = kwargs.get('ok', None)
    if ok is not None:
        print("all good!")
        sys.exit(0)

if __name__ == "__main__":
    args = parse_gnu_style_args()
    print("Parsed arguments:")
    for k, v in args.items():
        print(f"{k}: {v}")
    handle_args(**args)


