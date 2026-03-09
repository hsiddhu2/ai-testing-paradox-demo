#!/bin/bash
# Simulate CI/CD Pipeline Locally
# This runs the same checks as .github/workflows/ai_test_validation.yml

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

set -e  # Exit on any error (after venv activation)

echo "========================================================================"
echo "🚀 SIMULATING CI/CD PIPELINE LOCALLY"
echo "========================================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

echo "${BLUE}========================================${NC}"
echo "${BLUE}STRATEGY 1: MUTATION TESTING GATE${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Step 1: Run Tests
echo "${YELLOW}Step 1: Running Tests...${NC}"
if pytest tests/ -v --tb=short; then
    echo "${GREEN}✅ Tests PASSED${NC}"
else
    echo "${RED}❌ Tests FAILED - Build would be blocked${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Step 2: Code Coverage
echo "${YELLOW}Step 2: Checking Code Coverage (minimum 80%)...${NC}"
if pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80; then
    echo "${GREEN}✅ Coverage PASSED (≥80%)${NC}"
else
    echo "${RED}❌ Coverage FAILED (<80%) - Build would be blocked${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Step 3: Mutation Testing (informational)
echo "${YELLOW}Step 3: Running Mutation Testing (informational)...${NC}"
rm -f .mutmut-cache
if mutmut run --paths-to-mutate=src/ 2>&1 | tail -20; then
    echo ""
    mutmut results
    echo "${BLUE}ℹ️  Mutation testing complete (informational only)${NC}"
else
    echo "${YELLOW}⚠️  Mutation testing had issues (non-blocking)${NC}"
fi
echo ""

echo "${BLUE}========================================${NC}"
echo "${BLUE}STRATEGY 2: HOTSPOT ANALYSIS${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Step 4: Hotspot Analysis
echo "${YELLOW}Step 4: Running Regression Hotspot Analysis...${NC}"
if python scripts/hotspot_analyzer.py; then
    echo "${GREEN}✅ Hotspot analysis complete${NC}"
else
    echo "${YELLOW}⚠️  Hotspot analysis had issues${NC}"
fi
echo ""

echo "${BLUE}========================================${NC}"
echo "${BLUE}STRATEGY 3: GOVERNANCE CHECK${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Step 5: Governance Validation
echo "${YELLOW}Step 5: Running Governance Validation...${NC}"
if python scripts/governance_checker.py; then
    echo "${GREEN}✅ Governance checks PASSED${NC}"
else
    echo "${RED}❌ Governance checks FAILED - Build would be blocked${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Final Summary
echo "========================================================================"
echo "📊 CI/CD PIPELINE SUMMARY"
echo "========================================================================"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo "${GREEN}✅ ALL CHECKS PASSED - Ready to merge!${NC}"
    echo ""
    echo "This Pull Request would be approved by CI/CD automation."
else
    echo "${RED}❌ SOME CHECKS FAILED - Cannot merge${NC}"
    echo ""
    echo "This Pull Request would be BLOCKED by CI/CD automation."
    echo "Fix the failing checks before merging."
fi
echo "========================================================================"

exit $OVERALL_STATUS
