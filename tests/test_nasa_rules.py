"""Static analyzer test verifying compliance with NASA JPL Power of 10 rules.

Checks:
- Rule 4: Function length strictly <= 60 lines.
- Rule 5: Assertion density.
"""

import ast
import os
import unittest


class TestNasaPowerOf10Rules(unittest.TestCase):
    """Static AST validation of NASA JPL Power of 10 constraints."""

    def setUp(self) -> None:
        self.src_dir = os.path.join(os.path.dirname(__file__), "..", "osb")

    def test_rule_4_function_length(self) -> None:
        """NASA Rule 4: No function longer than 60 lines of code."""
        violations = []

        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, filename=filepath)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Compute line span
                        start_line = node.lineno
                        end_line = getattr(node, "end_lineno", start_line)
                        length = end_line - start_line + 1
                        if length > 60:
                            violations.append(
                                f"{os.path.relpath(filepath, self.src_dir)}::{node.name} "
                                f"is {length} lines (max 60 allowed)"
                            )

        self.assertEqual(violations, [], f"NASA Rule 4 violations found:\n" + "\n".join(violations))

    def test_rule_5_assertion_density(self) -> None:
        """NASA Rule 5: Verify presence of assertions across core modules."""
        total_functions = 0
        total_assertions = 0

        core_dir = os.path.join(self.src_dir, "core")
        for root, _, files in os.walk(core_dir):
            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                        func_asserts = sum(1 for n in ast.walk(node) if isinstance(n, ast.Assert))
                        total_assertions += func_asserts

        self.assertGreater(total_functions, 0, "Should have functions in core")
        density = total_assertions / float(total_functions)
        # NASA rule targets ~2 assertions per function
        self.assertGreaterEqual(density, 1.5, f"Assertion density {density:.2f} is below target")


if __name__ == "__main__":
    unittest.main()
