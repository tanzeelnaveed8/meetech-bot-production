# Meetech Lead Qualification Bot

AI-powered WhatsApp chatbot for automated lead qualification with intelligent scoring, human handover, and automated follow-ups.

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose (optional)

### 2. Installation

```bash
# Clone or extract the bot folder
cd meetech-bot-clean

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 3. Configuration

Required environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/meetech_bot

# Redis
REDIS_URL=redis://localhost:6379

# WhatsApp Business API
WHATSAPP_API_TOKEN=your_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=your_verify_token

# OpenAI API
OPENAI_API_KEY=your_openai_key
```

### 4. Database Setup

```bash
# Start PostgreSQL and Redis (using Docker)
docker-compose up -d

# Run migrations
alembic upgrade head
```

### 5. Start the Bot

```bash
# Start API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal: Start Celery worker (for follow-ups)
celery -A src.workers.celery_app worker --loglevel=info

# In another terminal: Start Celery beat (scheduler)
celery -A src.workers.celery_app beat --loglevel=info
```

### 6. Verify Installation

```bash
# Check health
curl http://localhost:8000/v1/health

# Check metrics
curl http://localhost:8000/v1/metrics
```

## Features

✅ **Instant Response** - < 1 second p95 response time
✅ **9-State Conversation Flow** - GREETING → INTENT → QUALIFICATION → SCORING → PROOF → CALL → HANDOVER → FOLLOW_UP → EXIT
✅ **Intelligent Lead Scoring** - 5-component scoring (budget, timeline, clarity, country, behavior)
✅ **Human Handover** - Seamless agent takeover for high-scoring leads (70+)
✅ **Automated Follow-ups** - 2h/24h/3d intervals, max 3 attempts
✅ **Proof Assets** - Strategic portfolio/case study injection
✅ **Admin Dashboard** - Analytics, bot control, blacklist management
✅ **GDPR Compliant** - Data export and deletion endpoints

## API Endpoints

### Webhook
- `GET /v1/webhook/whatsapp` - Webhook verification
- `POST /v1/webhook/whatsapp` - Receive messages

### Agent Dashboard
- `GET /v1/agent/conversations` - List conversations
- `POST /v1/agent/conversations/{id}/takeover` - Take control
- `POST /v1/agent/conversations/{id}/messages` - Send message

### Admin
- `POST /v1/admin/bot/pause` - Pause bot
- `POST /v1/admin/bot/resume` - Resume bot
- `GET /v1/admin/analytics` - View analytics
- `GET /v1/admin/proof-assets` - Manage proof assets

### GDPR
- `GET /v1/gdpr/data/{phone}` - Export user data
- `DELETE /v1/gdpr/data/{phone}` - Delete user data

### Monitoring
- `GET /v1/health` - Health check
- `GET /v1/metrics` - Prometheus metrics

## Architecture

```
src/
├── api/           # FastAPI routers (webhook, agent, admin, gdpr)
├── models/        # SQLAlchemy models (8 models + 6 enums)
├── services/      # Business logic (11 services)
├── repositories/  # Database access (7 repositories)
├── integrations/  # External APIs (WhatsApp, LLM, Calendar, CRM)
├── workers/       # Celery workers (follow-up, cleanup)
├── utils/         # Utilities (metrics, rate limiter, logger)
└── db/            # Database connections (PostgreSQL, Redis)
```

## Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Run deployment script
./scripts/deploy.sh production

# Create database backup
./scripts/backup_db.sh
```

## Monitoring

- **Prometheus Metrics**: `http://localhost:8000/v1/metrics`
- **Analytics Dashboard**: `http://localhost:8000/v1/admin/analytics`
- **Health Check**: `http://localhost:8000/v1/health`

## Optional Integrations

Configure in `.env` to enable:

- **Google Calendar**: `GOOGLE_CALENDAR_API_KEY`, `GOOGLE_CALENDAR_ID`
- **Calendly**: `CALENDLY_API_TOKEN`, `CALENDLY_EVENT_TYPE_URL`
- **Notion CRM**: `NOTION_API_TOKEN`, `NOTION_CONTACTS_DATABASE_ID`
- **HubSpot CRM**: `HUBSPOT_API_TOKEN`
- **Sentry**: `SENTRY_DSN`

## Troubleshooting

### Bot not responding
- Check WhatsApp webhook is configured correctly
- Verify `WHATSAPP_API_TOKEN` is valid
- Check logs: `docker-compose logs -f app`

### Database connection failed
- Ensure PostgreSQL is running: `docker-compose ps`
- Verify `DATABASE_URL` in `.env`
- Run migrations: `alembic upgrade head`

### Redis connection failed
- Ensure Redis is running: `docker-compose ps`
- Verify `REDIS_URL` in `.env`

### Slow response times
- Check Prometheus metrics: `/v1/metrics`
- Monitor database queries
- Scale workers: `celery -A src.workers.celery_app worker --concurrency=4`

## Support

For issues or questions, contact: support@meetech.com

## License

Proprietary - Meetech Dev Team
