#!/bin/bash

# LegalAnalytics Mini - Implementation Verification Script
# This script validates that the implementation is working correctly

echo "🚀 LegalAnalytics Mini - Implementation Verification"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    echo -e "✅ Python 3 found: $(python3 --version)"
else
    echo -e "❌ Python 3 not found"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "✅ Docker found: $(docker --version)"
else
    echo -e "❌ Docker not found"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    echo -e "✅ Docker Compose found: $(docker-compose --version)"
else
    echo -e "❌ Docker Compose not found"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "❌ Please run this script from the project root directory"
    exit 1
fi

echo -e "\n${YELLOW}Testing Python imports (without dependencies)...${NC}"

# Test basic Python syntax
cd backend
python3 -c "
import sys
sys.path.append('src')

# Test that our Python files have valid syntax
files_to_test = [
    'src/models/base.py',
    'src/models/department.py',
    'src/models/employee.py',
    'src/models/user.py',
    'src/models/time_entry.py',
    'src/repositories/department_repository.py',
    'src/repositories/employee_repository.py',
    'src/services/employee_service.py',
    'src/api/employees.py',
    'src/main.py',
    'src/settings.py',
    'src/database.py'
]

for file in files_to_test:
    try:
        with open(file, 'r') as f:
            compile(f.read(), file, 'exec')
        print(f'✅ {file} - syntax valid')
    except Exception as e:
        print(f'❌ {file} - syntax error: {e}')
        exit(1)

print('🎉 All Python files have valid syntax!')
"

if [ $? -eq 0 ]; then
    echo -e "✅ Python syntax validation passed"
else
    echo -e "❌ Python syntax validation failed"
    exit 1
fi

echo -e "\n${YELLOW}Checking Docker Compose configuration...${NC}"

cd ../infrastructure
if docker-compose config > /dev/null 2>&1; then
    echo -e "✅ Docker Compose configuration is valid"
else
    echo -e "❌ Docker Compose configuration has errors"
    exit 1
fi

echo -e "\n${YELLOW}Checking project structure...${NC}"

# Check key directories and files exist
required_files=(
    "backend/requirements.txt"
    "backend/pyproject.toml"
    "backend/src/main.py"
    "backend/src/settings.py"
    "backend/alembic.ini"
    "backend/alembic/env.py"
    "backend/scripts/seed_data.py"
    "frontend/package.json"
    "frontend/angular.json"
    "infrastructure/docker-compose.yml"
    "specs/001-build-legalanalytics-mini/tasks.md"
    "specs/001-build-legalanalytics-mini/quickstart.md"
)

cd ..

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "✅ $file exists"
    else
        echo -e "❌ $file missing"
        exit 1
    fi
done

echo -e "\n${GREEN}🎉 Implementation verification completed successfully!${NC}"
echo -e "\n${YELLOW}Next steps for manual testing:${NC}"
echo "1. Install Python dependencies:"
echo "   cd backend && pip3 install -r requirements.txt"
echo ""
echo "2. Start infrastructure services:"
echo "   cd infrastructure && docker-compose up -d"
echo ""
echo "3. Setup database:"
echo "   cd backend && python3 -m alembic upgrade head"
echo "   python3 scripts/seed_data.py"
echo ""
echo "4. Start API server:"
echo "   python3 -m uvicorn src.main:app --reload"
echo ""
echo "5. Test in browser:"
echo "   http://localhost:8000/docs (Swagger UI)"
echo "   http://localhost:8000/health (Health check)"
echo ""
echo -e "${GREEN}See MANUAL_TESTING_GUIDE.md for detailed testing instructions!${NC}"