#!/usr/bin/env python3
# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List

class RTMParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.mappings: Dict[str, List[str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if (isinstance(func, ast.Name) and func.id == "verifies") or \
                   (isinstance(func, ast.Attribute) and func.attr == "verifies"):
                    for arg in decorator.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            self.mappings.setdefault(arg.value, []).append(node.name)
        self.generic_visit(node)

def run_audit(req_file: str, test_dir: str, output_file: str) -> bool:
    with open(req_file, "r", encoding="utf-8") as f:
        reqs = json.load(f)

    parser = RTMParser()
    for py_file in Path(test_dir).rglob("test_*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            parser.visit(ast.parse(f.read(), filename=str(py_file)))

    rtm_data = []
    uncovered = []

    for req in reqs:
        req_id = req["id"]
        tests = parser.mappings.get(req_id, [])
        if not tests:
            uncovered.append(req_id)
        rtm_data.append({
            "requirement_id": req_id,
            "title": req.get("title", ""),
            "safety_level": req.get("safety_level", "STANDARD"),
            "verifying_tests": tests,
            "status": "VERIFIED" if tests else "UNCOVERED"
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rtm_data, f, indent=2)

    if uncovered:
        print(f"RTM AUDIT FAILED: Uncovered requirements: {uncovered}", file=sys.stderr)
        return False
    print("RTM AUDIT PASSED: 100% Requirements Traceability Verified.")
    return True

if __name__ == "__main__":
    success = run_audit("requirements.json", "tests", "RTM_MATRIX.json")
    sys.exit(0 if success else 1)
