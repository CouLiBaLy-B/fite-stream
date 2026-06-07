#!/usr/bin/env python3
"""Remove misplaced auto-generated docstrings that cause syntax errors."""

import ast
import os


def fix_file(filepath):
    """Try removing short docstring lines until the file parses."""
    with open(filepath) as f:
        lines = f.readlines()
    
    try:
        ast.parse("".join(lines))
        return 0  # Already OK
    except SyntaxError:
        pass
    
    removed = 0
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect auto-generated docstrings: short, single-line, triple-quoted
        if (stripped.startswith('"""') and stripped.endswith('."""')
                and len(stripped) < 60 and stripped.count('"""') == 2):
            
            # Test if removing this line fixes the syntax
            test = lines[:i] + lines[i+1:]
            try:
                ast.parse("".join(test))
                removed += 1
                continue  # Skip this line
            except SyntaxError:
                pass
        
        new_lines.append(line)
    
    if removed > 0:
        with open(filepath, "w") as f:
            f.writelines(new_lines)
    
    return removed


def main():
    total_fixed = 0
    total_broken = 0
    
    for dirpath, _, filenames in os.walk("fitstream"):
        if "__pycache__" in dirpath:
            continue
        for fname in sorted(filenames):
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, fname)
            
            n = fix_file(filepath)
            if n > 0:
                print(f"  Fixed {n} in {filepath}")
                total_fixed += n
    
    # Verify
    for dirpath, _, filenames in os.walk("fitstream"):
        if "__pycache__" in dirpath:
            continue
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, fname)
            try:
                with open(filepath) as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                print(f"  STILL BROKEN: {filepath}: line {e.lineno}")
                total_broken += 1
    
    print(f"\nRemoved {total_fixed} bad docstrings")
    if total_broken == 0:
        print("ALL FILES CLEAN")
    else:
        print(f"{total_broken} files still broken")


if __name__ == "__main__":
    main()
