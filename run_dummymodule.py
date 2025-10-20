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


def write_cli_flags(kwargs: Dict[str, Optional[str]], output_dir: str) -> None:
    """Write all CLI flags to cli.txt file."""
    cli_file_path = Path(output_dir) / "cli.txt"
    os.makedirs(output_dir, exist_ok=True)

    with open(cli_file_path, "w") as cli_file:
        for flag, value in kwargs.items():
            if value is None:
                cli_file.write(f"--{flag}\n")
            else:
                cli_file.write(f"--{flag} {value}\n")


def handle_failure_flag(kwargs: Dict[str, Optional[str]]) -> None:
    """Handle the --fail flag by raising an exception."""
    if kwargs.get("fail", None) is not None:
        raise RuntimeError("failing hard")


def handle_evaluation(kwargs: Dict[str, Optional[str]]) -> Optional[int]:
    """Handle expression evaluation and return the result."""

    evaluate = kwargs.get("evaluate")
    if evaluate is None:
        return None

    print("evaluating:", evaluate)
    try:
        input_value = resolve_input_value(kwargs)
        result = safe_eval_addmul(evaluate, input_value=input_value)
        print("result:", result)
        return result
    except Exception:
        raise


def write_named_output(name: str, output_dir: str, payload: Optional[int]) -> None:
    """Write output to {name}_data.json file."""
    filename = f"{name}_data.json"
    output_path = Path(output_dir) / filename
    print(f"Writing output to: {output_path}")

    with open(output_path, "w") as out_f:
        if payload is None:
            out_f.write(serialize("O" * 32, None))
        else:
            out_f.write(serialize(payload, None))


def write_generic_output(
    output_path: str, output_dir: str, payload: Optional[int]
) -> None:
    """Write output to a generic output file."""
    parent = Path(output_path).parent
    if output_dir != ".":
        parent = Path(output_dir) / parent

    os.makedirs(parent, exist_ok=True)
    full_path = parent / Path(output_path).name

    with open(full_path, "w") as out_f:
        if payload is None:
            out_f.write("A" * 32)
        else:
            out_f.write(serialize(payload, None))


def handle_ok_flag(kwargs: Dict[str, Optional[str]]) -> None:
    """Handle the --ok flag by exiting successfully."""
    if kwargs.get("ok", None) is not None:
        print("all good!")
        sys.exit(0)


def handle_args(**kwargs):
    """
    Main argument handler that processes all command line arguments.

    This function coordinates the various argument handling steps:
    1. Log CLI flags to file
    2. Handle special flags (fail, evaluate, etc.)
    3. Process output generation
    4. Handle exit conditions
    """
    global payload

    print("HANDLING", kwargs)

    # Get output directory early as it's used by multiple functions
    output_dir = kwargs.get("output_dir", ".")
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Log all CLI flags
    write_cli_flags(kwargs, output_dir)

    # Step 2: Handle special control flags
    handle_failure_flag(kwargs)

    # Step 3: Handle evaluation
    payload = handle_evaluation(kwargs)

    # Step 4: Generate output files
    print("out_dir:", output_dir)

    # Handle --name parameter output
    name = kwargs.get("name")
    if name is not None:
        write_named_output(name, output_dir, payload)

    # Handle --output parameter
    output_path = kwargs.get("output")
    if output_path is not None:
        write_generic_output(output_path, output_dir, payload)

    # Step 5: Handle exit conditions
    handle_ok_flag(kwargs)


def resolve_input_value(kwargs: Dict[str, Optional[str]]) -> str:
    """
    Resolve the input variable by reading from a JSON file.

    The --input flag should contain a label like "foo.var".
    This function will:
    1. Use "foo.var" as a literal flag name to look up
    2. Get the file path from the --foo.var flag
    3. Read the JSON file and extract the "result" field
    4. Return it as a string

    Args:
        kwargs: Dictionary of command line arguments

    Returns:
        String representation of the input value (defaults to "1" if no --input flag)
    """
    input_spec = kwargs.get("input")
    if input_spec is None:
        return "1"  # Default value

    # Get the file path from the flag with the same name as input_spec
    file_path = kwargs.get(input_spec)
    if file_path is None:
        raise ValueError(
            f"Flag --{input_spec} is required when using --input {input_spec}"
        )

    # The file_path is used directly

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if "result" not in data:
            raise ValueError(f"JSON file {file_path} does not contain a 'result' field")

        result = data["result"]

        # Convert to int to validate, then back to string
        int(result)
        return str(result)

    except FileNotFoundError:
        raise ValueError(f"Input file {file_path} not found")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file {file_path}")
    except (ValueError, TypeError) as e:
        if "invalid literal for int()" in str(e):
            raise ValueError(
                f"Result field in {file_path} is not a valid integer: {result}"
            )
        raise


def safe_eval_addmul(
    expr: str,
    *,
    input_value: str = "1",
    max_len: int = 512,
    max_terms: int = 128,
    max_factors: int = 128,
    max_digits_per_number: int = 6,
) -> int:
    """
    Safely evaluate an expression consisting only of integers, '+', '*', and the special variable 'input'.
    - Allowed: ASCII digits [0-9], '+', '*', 'input' keyword, and whitespace.
    - Grammar: term (op term)* where op ∈ {+, *}, term ∈ {number, 'input'}; i.e. no empty terms, no unary ops.
    - Evaluation: left-associative
    - Returns: int
    - Raises: ValueError if invalid input or limits passed; TypeError on wrong type.

    Parameters (simple guardrails):
      - input_value: value to substitute for 'input' variable (as string)
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

    # quick whitelist (only ASCII digits, operators, 'input', and whitespace allowed).
    if not re.fullmatch(r"[0-9+*\sinput]+", expr):
        raise ValueError("illegal characters detected")

    if not re.fullmatch(r"\s*(?:\d+|input)(?:\s*[+*]\s*(?:\d+|input))*\s*", expr):
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
            if f == "input":
                # Handle the special 'input' variable
                if not re.fullmatch(r"\d+", input_value):
                    raise ValueError("input_value must be a valid integer")
                if len(input_value) > max_digits_per_number:
                    raise ValueError("input_value too long")
                prod *= int(input_value)
            else:
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
