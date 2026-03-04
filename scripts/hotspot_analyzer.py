#!/usr/bin/env python3
"""
Regression Hotspot Analyzer (Strategy 2)
=========================================
Analyzes git history to identify high-risk code files.
Run this to find where AI test agents should focus.

Usage:
    python scripts/hotspot_analyzer.py
    python scripts/hotspot_analyzer.py --repo-path /path/to/repo --months 6
"""

import subprocess
import sys
from datetime import datetime, timedelta
from collections import Counter


def run_git_command(cmd, repo_path="."):
    """Execute a git command and return output lines."""
    try:
        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"Warning: git command failed: {result.stderr}")
            return []
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except FileNotFoundError:
        print("Error: git not found. Make sure git is installed.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Warning: git command timed out.")
        return []


def get_most_changed_files(repo_path=".", months=6):
    """Find files that change most frequently — high churn = high risk."""
    since_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    cmd = [
        "git", "log", f"--since={since_date}", "--name-only",
        "--pretty=format:", "--diff-filter=ACMR"
    ]
    lines = run_git_command(cmd, repo_path)
    file_counts = Counter(lines)

    # Filter to source code files only
    code_extensions = {".py", ".js", ".ts", ".java", ".cs", ".go", ".rb", ".rs"}
    code_files = {
        f: c for f, c in file_counts.items()
        if any(f.endswith(ext) for ext in code_extensions)
    }
    return dict(sorted(code_files.items(), key=lambda x: x[1], reverse=True)[:20])


def get_bugfix_files(repo_path=".", months=6):
    """Find files most associated with bug-fix commits."""
    since_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    keywords = ["fix", "bug", "patch", "hotfix", "resolve", "repair"]

    all_fix_files = []
    for keyword in keywords:
        cmd = [
            "git", "log", f"--since={since_date}",
            f"--grep={keyword}", "-i", "--name-only", "--pretty=format:"
        ]
        all_fix_files.extend(run_git_command(cmd, repo_path))

    return dict(Counter(all_fix_files).most_common(20))


def get_code_churn(repo_path=".", months=6):
    """Calculate code churn (lines added + deleted) per file."""
    since_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    cmd = [
        "git", "log", f"--since={since_date}", "--numstat", "--pretty=format:"
    ]
    lines = run_git_command(cmd, repo_path)

    churn = {}
    for line in lines:
        parts = line.split("\t")
        if len(parts) == 3 and parts[0] != "-":
            try:
                added = int(parts[0])
                deleted = int(parts[1])
                filename = parts[2]
                churn[filename] = churn.get(filename, 0) + added + deleted
            except ValueError:
                continue

    return dict(sorted(churn.items(), key=lambda x: x[1], reverse=True)[:20])


def calculate_risk_scores(change_freq, bugfix_freq, churn):
    """Combine all factors into a risk score per file."""
    all_files = set(change_freq.keys()) | set(bugfix_freq.keys()) | set(churn.keys())

    max_changes = max(change_freq.values()) if change_freq else 1
    max_fixes = max(bugfix_freq.values()) if bugfix_freq else 1
    max_churn = max(churn.values()) if churn else 1

    scores = {}
    for f in all_files:
        change_score = (change_freq.get(f, 0) / max_changes) * 40
        fix_score = (bugfix_freq.get(f, 0) / max_fixes) * 35
        churn_score = (churn.get(f, 0) / max_churn) * 25
        scores[f] = round(change_score + fix_score + churn_score, 1)

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def print_report(change_freq, bugfix_freq, churn, risk_scores):
    """Print the hotspot analysis report."""
    print("=" * 70)
    print("REGRESSION HOTSPOT ANALYSIS REPORT")
    print("=" * 70)

    print("\n## Top Files by Change Frequency (High Churn = High Risk)")
    print("-" * 50)
    for f, count in list(change_freq.items())[:10]:
        print(f"  {count:4d} changes  |  {f}")

    print("\n## Top Files by Bug-Fix Commits")
    print("-" * 50)
    for f, count in list(bugfix_freq.items())[:10]:
        print(f"  {count:4d} fixes    |  {f}")

    print("\n## Top Files by Code Churn (Lines Added + Deleted)")
    print("-" * 50)
    for f, c in list(churn.items())[:10]:
        print(f"  {c:6d} lines  |  {f}")

    print("\n## COMBINED RISK SCORES (0-100)")
    print("-" * 50)
    for f, score in list(risk_scores.items())[:15]:
        risk_level = "🔴 HIGH" if score >= 60 else "🟡 MEDIUM" if score >= 30 else "🟢 LOW"
        print(f"  {score:5.1f}  {risk_level}  |  {f}")

    print("\n## RECOMMENDATION")
    print("-" * 50)
    high_risk = [f for f, s in risk_scores.items() if s >= 60]
    if high_risk:
        print(f"  Direct AI test agent to prioritize these {len(high_risk)} high-risk files:")
        for f in high_risk[:5]:
            print(f"    → {f}")
    else:
        print("  No high-risk hotspots detected. Codebase is relatively stable.")

    print("\n" + "=" * 70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Regression Hotspot Analyzer")
    parser.add_argument("--repo-path", default=".", help="Path to git repository")
    parser.add_argument("--months", type=int, default=6, help="Analysis period in months")
    args = parser.parse_args()

    print(f"Analyzing git history for {args.repo_path} (last {args.months} months)...")

    change_freq = get_most_changed_files(args.repo_path, args.months)
    bugfix_freq = get_bugfix_files(args.repo_path, args.months)
    churn = get_code_churn(args.repo_path, args.months)
    risk_scores = calculate_risk_scores(change_freq, bugfix_freq, churn)

    print_report(change_freq, bugfix_freq, churn, risk_scores)


if __name__ == "__main__":
    main()
