# Python Environment Setup - Quick Fix

## 🐍 The Issue
You're getting Python environment issues because we need to set up a virtual environment first.

## ✅ Quick Solution (2 minutes)

### Step 1: Create Virtual Environment
```bash
cd /Users/wenxuan.zhou/PLP/plpmin/plp-mini/backend

# Create virtual environment
python3 -m venv venv

# Activate it (this is the key step!)
source venv/bin/activate

# You should see (venv) at the start of your terminal prompt
```

### Step 2: Install Dependencies
```bash
# Now install requirements (should work without issues)
pip install -r requirements.txt
```

### Step 3: Verify Installation
```bash
# Test that key packages are installed
python -c "import fastapi; print('FastAPI installed successfully')"
python -c "import sqlalchemy; print('SQLAlchemy installed successfully')"
```

## 🔧 Alternative: Use System Python (if virtual env doesn't work)

If virtual environment gives you trouble:

```bash
cd /Users/wenxuan.zhou/PLP/plpmin/plp-mini/backend

# Install directly with pip3 (system-wide)
pip3 install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic-settings python-multipart

# Or use --user flag to install for your user only
pip3 install --user -r requirements.txt
```

## 🚨 Common Issues & Fixes

### Issue 1: "pip: command not found"
```bash
# Use pip3 instead
pip3 install -r requirements.txt
```

### Issue 2: "Permission denied"
```bash
# Use --user flag
pip3 install --user -r requirements.txt
```

### Issue 3: "No module named 'venv'"
```bash
# Install venv if missing
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
```

### Issue 4: Virtual environment activation fails
```bash
# Try different activation method
cd /Users/wenxuan.zhou/PLP/plpmin/plp-mini/backend
python3 -m venv venv

# Try this activation instead
. venv/bin/activate

# Or this one
bash venv/bin/activate
```

## 📋 Step-by-Step Verification

Run these commands one by one to verify each step:

```bash
# 1. Check Python version
python3 --version

# 2. Navigate to backend directory
cd /Users/wenxuan.zhou/PLP/plpmin/plp-mini/backend
pwd

# 3. Create virtual environment
python3 -m venv venv
ls -la  # You should see a 'venv' directory

# 4. Activate virtual environment
source venv/bin/activate
# Your prompt should now show (venv)

# 5. Upgrade pip in virtual environment
pip install --upgrade pip

# 6. Install requirements
pip install -r requirements.txt

# 7. Test imports
python -c "import fastapi, sqlalchemy, pydantic; print('All packages installed!')"
```

## 🎯 Expected Output

When everything works, you should see:
```
(venv) your-username@computer backend % python -c "import fastapi, sqlalchemy, pydantic; print('All packages installed!')"
All packages installed!
```

## 🚀 Quick Test Script

Once dependencies are installed, test the implementation:

```bash
# Still in activated virtual environment
python -c "
import sys
sys.path.append('src')
from main import app
print('✅ FastAPI app loads successfully!')

from models.employee import Employee
print('✅ Models import successfully!')

from services.employee_service import EmployeeService
print('✅ Services import successfully!')

print('🎉 Implementation is ready to run!')
"
```

## 🐛 Still Having Issues?

If you're still having problems, try this minimal test:

```bash
# Install just the essential packages manually
pip3 install fastapi uvicorn

# Create a simple test file
cat > test_fastapi.py << 'EOF'
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Run the test
python3 test_fastapi.py
```

Then go to http://localhost:8000 - if you see `{"Hello": "World"}`, FastAPI is working!

Let me know what specific error message you're getting and I can provide a more targeted fix! 🔧