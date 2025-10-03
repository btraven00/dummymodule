#!/usr/bin/env python

"""
Just a dummy module to try stuff with omnibenchmark.
Useful for debugging; i.e. to make modules return arbitrary failures, sleep, etc.
"""

import json
import re
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
        if arg.startswith("--"):
            flag = arg[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args[flag] = argv[i + 1]
                i += 2
            else:
                args[flag] = None
                i += 1
        else:
            # Handle non-flag arguments if needed
            i += 1
    return args


payload = None


def serialize(payload, error):
    return json.dumps({"result": payload, "error": error})


def handle_args(**kwargs):
    global payload

    print("HANDLING", kwargs)

    if kwargs.get("fail", None) is not None:
        raise RuntimeError("failing hard")

    if (evaluate := kwargs.get("evaluate", None)) is not None:
        print("evaluating:", evaluate)
        try:
            payload = safe_eval_addmul(evaluate)
            print("result:", payload)
        except Exception:
            raise

    print("HANDLE")

    out_dir = kwargs.get("output_dir", ".")
    print("out_dir:", out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if (out := kwargs.get("output", None)) is not None:
        parent = Path(out).parent
        if out_dir is not None:
            parent = out_dir / parent
        os.makedirs(parent, exist_ok=True)
        with open(Path(parent / Path(out).name).as_posix(), "w") as out_f:
            if payload is None:
                out_f.write("A" * 32)
            else:
                out_f.write(serialize(payload, None))

    if kwargs.get("ok", None) is not None:
        print("all good!")
        sys.exit(0)


def safe_eval_addmul(
    expr: str,
    *,
    max_len: int = 512,
    max_terms: int = 128,
    max_factors: int = 128,
    max_digits_per_number: int = 6,
) -> int:
    """
    Safely evaluate an expression consisting only of integers, '+' and '*'.
    - Allowed: ASCII digits [0-9], '+', '*', and whitespace.
    - Grammar: number (op number)* where op ∈ {+, *}; i.e. no empty terms, no unary ops.
    - Evaluation: left-associative
    - Returns: int
    - Raises: ValueError if invalid input or limits passed; TypeError on wrong type.

    Parameters (simple guardrails):
      - max_len: max total expression length
      - max_terms: max additive terms (split by '+')
      - max_factors: max multiplicative factors per term (split by '*')
      - max_digits_per_number: max digits allowed per number literal
    """
    # Some sanity checks first of all:
    if not isinstance(expr, str):
        raise TypeError("expr must be a string")
    if not expr or len(expr) > max_len:
        raise ValueError("invalid length")

    # quick whitelist (only ASCII allowd).
    if not re.fullmatch(r"[0-9+*\s]+", expr):
        raise ValueError("illegal characters detected")

    if not re.fullmatch(r"\s*\d+(?:\s*[+*]\s*\d+)*\s*", expr):
        raise ValueError("invalid structure")

    expr_stripped = expr.strip()

    terms = re.split(r"\s*\+\s*", expr_stripped)
    if len(terms) > max_terms:
        raise ValueError("too many additive terms")

    total = 0
    for term in terms:
        # Each term is one or more factors separated by '*'
        factors = re.split(r"\s*\*\s*", term)
        if not factors or any(f == "" for f in factors):
            raise ValueError("empty factor")
        if len(factors) > max_factors:
            raise ValueError("too many multiplicative factors")

        prod = 1
        for f in factors:
            # Enforce digits-only per number and digit count cap
            if not re.fullmatch(r"\d+", f):
                raise ValueError("non-digit in number")
            if len(f) > max_digits_per_number:
                raise ValueError("number literal too long")
            # Leading zeros are allowed; Python int handles big integers.
            prod *= int(f)

        total += prod

    return total


if __name__ == "__main__":
    args = parse_gnu_style_args()
    print("Parsed arguments:")
    for k, v in args.items():
        print(f"{k}: {v}")
    handle_args(**args)
