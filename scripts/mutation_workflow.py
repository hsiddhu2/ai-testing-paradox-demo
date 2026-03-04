#!/usr/bin/env python3
"""
Automated Mutation Testing Workflow (Strategy 1)
=================================================
Demonstrates the complete GenAI → mutmut → refinement workflow.

Usage:
    python scripts/mutation_workflow.py
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"CMD:  {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.stdout:
            print(result.stdout[:2000])
        if result.stderr and result.returncode != 0:
            print(f"STDERR: {result.stderr[:500]}")
        return result.returncode == 0
    except FileNotFoundError:
        print(f"Error: Command '{cmd[0]}' not found. Install required tools.")
        return False
    except subprocess.TimeoutExpired:
        print("Warning: Command timed out (5 min limit).")
        return False


def main():
    print("=" * 60)
    print("AI TEST VALIDATION WORKFLOW")
    print("Strategy 1: Mutation Testing with mutmut")
    print("=" * 60)

    # Step 1: Run AI-generated tests
    print("\n" + "🤖" * 30)
    print("PHASE 1: Run AI-Generated Tests (simulated)")
    print("🤖" * 30)

    run_command(
        ["pytest", "tests/test_auth_ai_generated.py", "-v", "--tb=short"],
        "Running AI-generated tests"
    )

    run_command(
        ["pytest", "tests/test_auth_ai_generated.py",
         "--cov=src/auth_service", "--cov-report=term-missing"],
        "Checking coverage of AI-generated tests"
    )

    # Step 2: Run mutation testing on AI-generated tests
    print("\n" + "🧬" * 30)
    print("PHASE 2: Mutation Testing — The Truth Revealed")
    print("🧬" * 30)

    run_command(
        ["mutmut", "run", "--paths-to-mutate=src/auth_service.py",
         "--tests-dir=tests/", "--runner=python -m pytest tests/test_auth_ai_generated.py -x --tb=no -q"],
        "Running mutation testing against AI-generated tests"
    )

    run_command(
        ["mutmut", "results"],
        "Viewing surviving mutants (bugs the AI tests missed)"
    )

    # Step 3: Run mutation-hardened tests
    print("\n" + "💪" * 30)
    print("PHASE 3: Mutation-Hardened Tests — After Human Refinement")
    print("💪" * 30)

    # Clear previous mutmut cache
    run_command(["rm", "-f", ".mutmut-cache"], "Clearing previous mutation cache")

    run_command(
        ["pytest", "tests/test_auth_mutation_hardened.py", "-v", "--tb=short"],
        "Running mutation-hardened tests"
    )

    run_command(
        ["pytest", "tests/test_auth_mutation_hardened.py",
         "--cov=src/auth_service", "--cov-report=term-missing"],
        "Checking coverage of mutation-hardened tests"
    )

    run_command(
        ["mutmut", "run", "--paths-to-mutate=src/auth_service.py",
         "--tests-dir=tests/", "--runner=python -m pytest tests/test_auth_mutation_hardened.py -x --tb=no -q"],
        "Running mutation testing against mutation-hardened tests"
    )

    run_command(
        ["mutmut", "results"],
        "Viewing results — fewer survivors!"
    )

    # Summary
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    print("""
    Compare the two phases:

    Phase 2 (AI-Generated Tests):
    → High coverage but LOW mutation kill rate
    → Many mutants survived = many real bugs missed

    Phase 3 (Mutation-Hardened Tests):
    → High coverage AND HIGH mutation kill rate
    → Fewer surviving mutants = better bug detection

    KEY INSIGHT: Coverage lies. Mutation kill rate tells the truth.
    """)


if __name__ == "__main__":
    main()
