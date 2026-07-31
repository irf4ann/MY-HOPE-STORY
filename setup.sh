#!/bin/bash
# Setup script for My Hope Story project

echo "🚀 My Hope Story - Development Setup"
echo "===================================="
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python -m venv venv
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Edit .env with your configuration!"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p media
mkdir -p staticfiles
mkdir -p logs

# Run migrations
echo ""
echo "🗄️  Running migrations..."
python manage.py migrate

# Create demo users
echo ""
echo "👥 Creating demo users..."
python manage.py create_demo_users

# Create superuser if not exists
echo ""
echo "👨‍💼 Creating superuser (follow prompts)..."
python manage.py createsuperuser

# Collect static files
echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "1. Activate virtual environment: source venv/Scripts/activate (Windows) or source venv/bin/activate (Linux/Mac)"
echo "2. Run development server: python manage.py runserver"
echo "3. Access admin at: http://localhost:8000/admin/"
echo "4. Access API at: http://localhost:8000/api/v1/"
echo "5. API docs at: http://localhost:8000/api/v1/docs/swagger/"
echo ""
