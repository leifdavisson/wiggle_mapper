#!/usr/bin/env python3
# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
"""AST-based deterministic mutation testing suite."""
import ast
import importlib
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

SRC_DIR = Path("/home/leifdavisson/wiggle_mapper/src")

class Mutator(ast.NodeTransformer):
    def __init__(self, target_node_id: int, mutation_type: str):
        self.current_id = 0
        self.target_node_id = target_node_id
        self.mutation_type = mutation_type
        self.applied = False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        for idx, op in enumerate(node.ops):
            self.current_id += 1
            if self.current_id == self.target_node_id and not self.applied:
                if isinstance(op, ast.Lt):
                    node.ops[idx] = ast.LtE()
                elif isinstance(op, ast.LtE):
                    node.ops[idx] = ast.Lt()
                elif isinstance(op, ast.Gt):
                    node.ops[idx] = ast.GtE()
                elif isinstance(op, ast.GtE):
                    node.ops[idx] = ast.Gt()
                elif isinstance(op, ast.Eq):
                    node.ops[idx] = ast.NotEq()
                elif isinstance(op, ast.NotEq):
                    node.ops[idx] = ast.Eq()
                self.applied = True
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.current_id += 1
        if self.current_id == self.target_node_id and not self.applied:
            if isinstance(node.op, ast.Add):
                node.op = ast.Sub()
            elif isinstance(node.op, ast.Sub):
                node.op = ast.Add()
            elif isinstance(node.op, ast.Mult):
                node.op = ast.Div()
            elif isinstance(node.op, ast.Div):
                node.op = ast.Mult()
            self.applied = True
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.current_id += 1
        if self.current_id == self.target_node_id and not self.applied:
            if isinstance(node.op, ast.And):
                node.op = ast.Or()
            elif isinstance(node.op, ast.Or):
                node.op = ast.And()
            self.applied = True
        return self.generic_visit(node)

def count_mutation_points(tree: ast.AST) -> int:
    class Counter(ast.NodeVisitor):
        def __init__(self):
            self.count = 0
        def visit_Compare(self, node):
            self.count += len(node.ops)
            self.generic_visit(node)
        def visit_BinOp(self, node):
            self.count += 1
            self.generic_visit(node)
        def visit_BoolOp(self, node):
            self.count += 1
            self.generic_visit(node)
    c = Counter()
    c.visit(tree)
    return c.count

def run_mutation_analysis() -> Tuple[int, int, List[str]]:
    total_mutants = 0
    killed_mutants = 0
    survived: List[str] = []

    py_files = [f for f in SRC_DIR.glob("*.py") if f.name != "__init__.py" and f.name != "models.py"]

    for py_file in py_files:
        orig_code = py_file.read_text(encoding="utf-8")
        orig_ast = ast.parse(orig_code)
        num_points = count_mutation_points(orig_ast)

        for target_id in range(1, num_points + 1):
            mutated_ast = ast.parse(orig_code)
            mutator = Mutator(target_id, "")
            mutated_ast = mutator.visit(mutated_ast)
            ast.fix_missing_locations(mutated_ast)

            if not mutator.applied:
                continue

            total_mutants += 1
            mutated_code = ast.unparse(mutated_ast)

            # Write mutated file
            py_file.write_text(mutated_code, encoding="utf-8")

            # Run pytest
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--disable-warnings", "tests/"],
                cwd="/home/leifdavisson/wiggle_mapper",
                capture_output=True,
                text=True
            )

            if proc.returncode != 0:
                killed_mutants += 1
            else:
                survived.append(f"{py_file.name} - Mutant #{target_id}")

        # Restore original code
        py_file.write_text(orig_code, encoding="utf-8")

    return total_mutants, killed_mutants, survived

if __name__ == "__main__":
    print("==================================================")
    print("      Active Mutation Score Analysis & Healing")
    print("==================================================")
    total, killed, survived = run_mutation_analysis()
    score = (killed / total * 100) if total > 0 else 100.0
    print(f"Total Mutants Evaluated: {total}")
    print(f"Killed Mutants:          {killed}")
    print(f"Surviving Mutants:       {len(survived)}")
    print(f"Mutation Score (MS):     {score:.1f}%")

    if survived:
        print("\nSurviving Mutant Locations:")
        for s in survived:
            print(f"  - {s}")

    if score >= 90.0:
        print("\n✓ PASSED: Mutation Score >= 90% threshold achieved.")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Mutation Score < 90%. Active healing loop required.")
        sys.exit(1)
