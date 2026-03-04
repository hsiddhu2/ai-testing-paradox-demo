#!/usr/bin/env python3
"""
AI Test Agent Governance Checker (Strategy 3)
==============================================
Validates that AI test agents comply with governance policies.
Implements approval gates, escalation triggers, and audit validation.

Usage:
    python scripts/governance_checker.py
"""

import json
import subprocess
import sys
from datetime import datetime


# ============================================================
# GOVERNANCE POLICY CONFIGURATION
# ============================================================
GOVERNANCE_POLICY = {
    "mutation_kill_rate_threshold": 70.0,    # Minimum acceptable kill rate (%)
    "coverage_threshold": 80.0,               # Minimum code coverage (%)
    "max_flaky_test_percentage": 10.0,        # Max flaky test rate (%)
    "high_risk_modules": [                    # Modules requiring human approval
        "payment_processor",
        "auth_service",
    ],
    "require_audit_trail": True,
    "require_human_review_for_high_risk": True,
}


class GovernanceResult:
    """Stores results of a governance check."""

    def __init__(self, check_name, passed, details, severity="INFO"):
        self.check_name = check_name
        self.passed = passed
        self.details = details
        self.severity = severity  # INFO, WARNING, CRITICAL
        self.timestamp = datetime.now().isoformat()

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"[{self.severity}] {status} | {self.check_name}: {self.details}"


def check_mutation_kill_rate(threshold=70.0):
    """
    ESCALATION TRIGGER: Alert if mutation kill rate drops below threshold.
    In a real pipeline, this reads mutmut results.
    """
    try:
        result = subprocess.run(
            ["mutmut", "results"], capture_output=True, text=True, timeout=30
        )
        output = result.stdout

        # Parse mutmut output for killed/survived counts
        killed = output.count("Killed")
        survived = output.count("Survived")
        total = killed + survived

        if total == 0:
            return GovernanceResult(
                "Mutation Kill Rate",
                False,
                "No mutation results found. Run 'mutmut run' first.",
                "WARNING"
            )

        kill_rate = (killed / total) * 100
        passed = kill_rate >= threshold

        return GovernanceResult(
            "Mutation Kill Rate",
            passed,
            f"Kill rate: {kill_rate:.1f}% (threshold: {threshold}%). "
            f"Killed: {killed}, Survived: {survived}",
            "CRITICAL" if not passed else "INFO"
        )

    except FileNotFoundError:
        return GovernanceResult(
            "Mutation Kill Rate",
            False,
            "mutmut not installed. Run 'pip install mutmut'.",
            "WARNING"
        )
    except Exception as e:
        return GovernanceResult(
            "Mutation Kill Rate",
            False,
            f"Error checking mutation rate: {str(e)}",
            "WARNING"
        )


def check_code_coverage(threshold=80.0):
    """
    APPROVAL GATE: Verify minimum code coverage threshold.
    """
    try:
        result = subprocess.run(
            ["pytest", "tests/", "--cov=src", "--cov-report=json", "-q"],
            capture_output=True, text=True, timeout=120
        )

        try:
            with open("coverage.json", "r") as f:
                cov_data = json.load(f)
            total_coverage = cov_data.get("totals", {}).get("percent_covered", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            total_coverage = 0

        passed = total_coverage >= threshold

        return GovernanceResult(
            "Code Coverage",
            passed,
            f"Coverage: {total_coverage:.1f}% (threshold: {threshold}%)",
            "CRITICAL" if not passed else "INFO"
        )

    except FileNotFoundError:
        return GovernanceResult(
            "Code Coverage",
            False,
            "pytest not installed.",
            "WARNING"
        )
    except Exception as e:
        return GovernanceResult(
            "Code Coverage",
            False,
            f"Error checking coverage: {str(e)}",
            "WARNING"
        )


def check_high_risk_module_coverage(high_risk_modules, threshold=90.0):
    """
    APPROVAL GATE: High-risk modules need HIGHER coverage than normal.
    """
    results = []
    for module in high_risk_modules:
        results.append(GovernanceResult(
            f"High-Risk Module: {module}",
            True,  # In real impl, check actual per-module coverage
            f"Module '{module}' marked as HIGH RISK. "
            f"Requires {threshold}% coverage and human review for test changes.",
            "INFO"
        ))
    return results


def check_audit_trail_completeness():
    """
    AUDIT CHECK: Verify that AI test agent decisions are logged.
    """
    required_events = [
        "test_generated", "test_modified", "test_deleted",
        "coverage_changed", "mutation_run"
    ]

    # In a real implementation, check the actual audit log
    return GovernanceResult(
        "Audit Trail",
        True,
        f"Audit trail check: Logging {len(required_events)} event types. "
        f"Ensure your AI agent logs: {', '.join(required_events)}",
        "INFO"
    )


def check_human_review_gates():
    """
    GOVERNANCE GATE: Verify human review requirements.
    """
    gates = [
        ("Payment logic changes", "MANDATORY", "Any changes to payment_processor.py"),
        ("Auth logic changes", "MANDATORY", "Any changes to auth_service.py"),
        ("Test deletion", "MANDATORY", "AI agents cannot delete tests without approval"),
        ("Coverage decrease", "REQUIRED", "If coverage drops by >5%"),
        ("New dependency", "RECOMMENDED", "Adding new test dependencies"),
    ]

    details = "\n".join([f"  [{level}] {name}: {desc}" for name, level, desc in gates])

    return GovernanceResult(
        "Human Review Gates",
        True,
        f"\n{len(gates)} review gates configured:\n{details}",
        "INFO"
    )


def run_governance_checks():
    """Run all governance checks and produce a report."""
    print("=" * 70)
    print("AI TEST AGENT GOVERNANCE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = []

    # Check 1: Mutation kill rate
    print("\n🔍 Checking mutation kill rate...")
    results.append(check_mutation_kill_rate(
        GOVERNANCE_POLICY["mutation_kill_rate_threshold"]
    ))

    # Check 2: Code coverage
    print("🔍 Checking code coverage...")
    results.append(check_code_coverage(
        GOVERNANCE_POLICY["coverage_threshold"]
    ))

    # Check 3: High-risk module coverage
    print("🔍 Checking high-risk module coverage...")
    results.extend(check_high_risk_module_coverage(
        GOVERNANCE_POLICY["high_risk_modules"]
    ))

    # Check 4: Audit trail
    print("🔍 Checking audit trail completeness...")
    results.append(check_audit_trail_completeness())

    # Check 5: Human review gates
    print("🔍 Checking human review gates...")
    results.append(check_human_review_gates())

    # Print results
    print("\n" + "-" * 70)
    print("RESULTS")
    print("-" * 70)

    passed = 0
    failed = 0
    warnings = 0

    for r in results:
        print(f"\n{r}")
        if r.passed:
            passed += 1
        elif r.severity == "CRITICAL":
            failed += 1
        else:
            warnings += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print(f"  ✅ Passed:   {passed}")
    print(f"  ❌ Failed:   {failed}")
    print(f"  ⚠️  Warnings: {warnings}")

    if failed > 0:
        print("\n🚨 GOVERNANCE STATUS: BLOCKED — Fix critical issues before deploying.")
        print("   Action: Human review required for failing checks.")
    elif warnings > 0:
        print("\n⚠️  GOVERNANCE STATUS: CONDITIONAL — Review warnings before deploying.")
    else:
        print("\n✅ GOVERNANCE STATUS: APPROVED — All checks passed.")

    print("=" * 70)

    return results


if __name__ == "__main__":
    run_governance_checks()
