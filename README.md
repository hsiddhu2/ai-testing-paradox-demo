# The AI Testing Paradox — Demo Project
## Three Strategies for Validating AI Test Agents

This project accompanies the talk **"The AI Testing Paradox: How to Trust Autonomous Agents That Validate Your Code"** at TestFormation 2026 (TMMi America).

It demonstrates three validation strategies with hands-on examples:

1. **Strategy 1: Mutation Testing** — Prove AI-generated tests catch real bugs
2. **Strategy 2: Regression Hotspot Prediction** — Focus testing on high-risk code
3. **Strategy 3: Human-in-the-Loop Governance** — Automated oversight patterns

---

## Quick Start

```bash
# Clone the project
git clone <your-repo-url>
cd ai-testing-paradox-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (Note: mutmut 2.4.5 is required - newer versions have CLI changes)
pip install -r requirements.txt

# Run the test suite
pytest tests/ -v

# Run code coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Run mutation testing (Strategy 1)
mutmut run --paths-to-mutate=src/

# View mutation results
mutmut results

# Run hotspot analysis (Strategy 2)
python scripts/hotspot_analyzer.py

# Run governance checker (Strategy 3)
python scripts/governance_checker.py
```

---

## Project Structure

```
ai-testing-paradox-demo/
├── src/
│   ├── __init__.py
│   ├── auth_service.py         # Authentication module (complex, realistic)
│   ├── payment_processor.py    # Payment processing (high-risk, governance-critical)
│   └── user_manager.py         # User management (moderate complexity)
├── tests/
│   ├── __init__.py
│   ├── test_auth_ai_generated.py         # AI-generated tests (intentionally weak)
│   ├── test_auth_mutation_hardened.py    # Tests improved via mutation testing
│   ├── test_auth_additional_mutants.py   # Additional tests targeting survivors
│   ├── test_payment_processor.py         # Payment tests with governance checks
│   └── test_user_manager.py              # User management tests
├── scripts/
│   ├── hotspot_analyzer.py     # Strategy 2: Git hotspot analysis
│   ├── governance_checker.py   # Strategy 3: Governance validation
│   └── mutation_workflow.py    # Strategy 1: Automated mutation workflow
├── .github/
│   └── workflows/
│       └── ai_test_validation.yml  # CI/CD with all 3 strategies
├── setup.cfg                   # mutmut configuration
├── requirements.txt            # Python dependencies (mutmut 2.4.5 required)
├── simulate_ci.sh              # Local CI/CD simulation script
└── README.md
```

---

## Strategy 1: Mutation Testing Demo

### Step 1: See the problem (AI-generated tests look good but miss bugs)
```bash
# Run AI-generated tests — they all pass!
pytest tests/test_auth_ai_generated.py -v

# Check coverage — looks impressive!
pytest tests/test_auth_ai_generated.py --cov=src/auth_service --cov-report=term-missing
```

### Step 2: Run mutation testing to reveal the truth
```bash
# Clear any previous mutation cache
rm -f .mutmut-cache

# Run mutmut against AI-generated tests only
mutmut run --paths-to-mutate=src/auth_service.py --tests-dir=tests/ --runner="python -m pytest tests/test_auth_ai_generated.py -x --tb=no -q"

# See surviving mutants (bugs the tests missed!)
mutmut results
mutmut show 1  # Inspect first surviving mutant
```

### Step 3: Compare with mutation-hardened tests
```bash
# Clear previous cache
rm -f .mutmut-cache

# Run mutation-hardened tests (uses setup.cfg configuration)
mutmut run

# Compare kill rates — much better!
mutmut results
```

---

## Strategy 2: Hotspot Analysis Demo

```bash
# Run the hotspot analyzer
python scripts/hotspot_analyzer.py

# This analyzes git history and outputs:
# - Top 20 most frequently changed files
# - Files with most bug-fix commits
# - Code churn per file
# - Risk score combining all factors
```

---

## Strategy 3: Governance Demo

```bash
# Run the governance checker
python scripts/governance_checker.py

# This validates:
# - Mutation kill rate thresholds
# - Coverage on hotspot files
# - Audit trail completeness
# - Approval gate compliance
```

---

## Local CI/CD Simulation

Run all three strategies locally (simulates the GitHub Actions workflow):

```bash
# Make sure you're in the project root with venv activated
./simulate_ci.sh

# This runs:
# 1. All tests
# 2. Coverage check (minimum 80%)
# 3. Mutation testing
# 4. Hotspot analysis
# 5. Governance validation
```

---

## Learning Flow

1. Start with `src/auth_service.py` — read the code
2. Run `tests/test_auth_ai_generated.py` — see them pass with high coverage
3. Run `mutmut` — discover surviving mutants
4. Read `tests/test_auth_mutation_hardened.py` — see how targeted tests kill mutants
5. Run `scripts/hotspot_analyzer.py` — see how git history reveals risk
6. Run `scripts/governance_checker.py` — see automated governance in action
