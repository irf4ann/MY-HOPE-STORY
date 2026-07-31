@echo off
REM Setup script for My Hope Story project (Windows)

echo.
echo 🚀 My Hope Story - Development Setup (Windows)
echo ===============================================
echo.

REM Check Python version
python --version
echo ✓ Python is installed
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Copy environment template
if not exist .env (
    echo.
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Edit .env with your configuration!
) else (
    echo ✓ .env file already exists
)

REM Create necessary directories
echo.
echo 📁 Creating directories...
if not exist media mkdir media
if not exist staticfiles mkdir staticfiles
if not exist logs mkdir logs

REM Run migrations
echo.
echo 🗄️  Running migrations...
python manage.py migrate

REM Create demo users
echo.
echo 👥 Creating demo users...
python manage.py create_demo_users

REM Create superuser
echo.
echo 👨‍💼 Creating superuser (follow prompts)...
python manage.py createsuperuser

REM Collect static files
echo.
echo 📦 Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ✅ Setup complete!
echo.
echo 📚 Next steps:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run development server: python manage.py runserver
echo 3. Access admin at: http://localhost:8000/admin/
echo 4. Access API at: http://localhost:8000/api/v1/
echo 5. API docs at: http://localhost:8000/api/v1/docs/swagger/
echo.
pause
