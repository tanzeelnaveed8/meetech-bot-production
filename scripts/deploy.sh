#!/bin/bash

# Deployment script for Meetech Lead Qualification Bot
# Usage: ./scripts/deploy.sh [environment]
# Environments: development, staging, production

set -e  # Exit on error

ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Deploying Meetech Lead Qualification Bot"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

# Load environment variables
if [ -f "$PROJECT_ROOT/.env.$ENVIRONMENT" ]; then
    echo "Loading environment variables from .env.$ENVIRONMENT"
    export $(cat "$PROJECT_ROOT/.env.$ENVIRONMENT" | grep -v '^#' | xargs)
else
    echo "Warning: .env.$ENVIRONMENT not found, using .env"
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Step 1: Pre-deployment checks
echo ""
echo "Step 1: Running pre-deployment checks..."
python "$SCRIPT_DIR/validate_quickstart.py" || {
    echo "Pre-deployment validation failed!"
    exit 1
}

# Step 2: Run tests
echo ""
echo "Step 2: Running tests..."
pytest tests/ -v --cov=src --cov-report=term-missing || {
    echo "Tests failed!"
    exit 1
}

# Step 3: Security scanning
echo ""
echo "Step 3: Running security scan..."
bandit -r src/ -f json -o bandit-report.json || {
    echo "Security scan found issues!"
    exit 1
}

# Step 4: Build Docker images
echo ""
echo "Step 4: Building Docker images..."
docker-compose -f docker-compose.yml build || {
    echo "Docker build failed!"
    exit 1
}

# Step 5: Database backup (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo ""
    echo "Step 5: Creating database backup..."
    bash "$SCRIPT_DIR/backup_db.sh" || {
        echo "Database backup failed!"
        exit 1
    }
fi

# Step 6: Run database migrations
echo ""
echo "Step 6: Running database migrations..."
alembic upgrade head || {
    echo "Database migration failed!"
    exit 1
}

# Step 7: Deploy services
echo ""
echo "Step 7: Deploying services..."
docker-compose -f docker-compose.yml up -d || {
    echo "Service deployment failed!"
    exit 1
}

# Step 8: Health check
echo ""
echo "Step 8: Running health check..."
sleep 10  # Wait for services to start

HEALTH_URL="${API_URL:-http://localhost:8000}/v1/health"
HEALTH_RESPONSE=$(curl -s "$HEALTH_URL")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "Health check passed!"
else
    echo "Health check failed!"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# Step 9: Start Celery workers
echo ""
echo "Step 9: Starting Celery workers..."
docker-compose -f docker-compose.yml exec -d app celery -A src.workers.celery_app worker --loglevel=info
docker-compose -f docker-compose.yml exec -d app celery -A src.workers.celery_app beat --loglevel=info

# Step 10: Post-deployment verification
echo ""
echo "Step 10: Post-deployment verification..."
echo "Checking API endpoints..."
curl -s "$HEALTH_URL" | jq .
curl -s "${API_URL:-http://localhost:8000}/v1/metrics" | head -n 20

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "Environment: $ENVIRONMENT"
echo "API URL: ${API_URL:-http://localhost:8000}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Monitor logs: docker-compose logs -f"
echo "2. Check metrics: ${API_URL:-http://localhost:8000}/v1/metrics"
echo "3. View admin dashboard: ${API_URL:-http://localhost:8000}/v1/admin/analytics"
echo ""
