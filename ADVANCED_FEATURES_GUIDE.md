# Advanced Features Implementation Guide

This document outlines all the advanced features implemented in My Hope Story and how to configure them.

## Overview

Your platform now includes 7 major advanced features:

1. **Celery + Email Notifications** - Async task queue for email delivery
2. **Stripe Payment Integration** - Handle donations and subscriptions
3. **Elasticsearch Search** - Full-text and faceted search
4. **Recommendation Engine** - Personalized story recommendations
5. **WebSockets/Real-time** - Live notifications and chat
6. **Analytics Dashboard** - Comprehensive metrics and insights
7. **AI Content Moderation** - Smart content filtering and moderation

---

## 1. Celery + Email Notifications

### Setup

```bash
# Install dependencies (already in requirements.txt)
pip install -r requirements.txt

# Start Celery worker
celery -A myhopestory worker -l info

# Start Celery beat (for scheduled tasks)
celery -A myhopestory beat -l info
```

### Configuration

Add to your `.env` file:
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@myhopestory.com
```

### Usage

```python
# Send email asynchronously
from notifications.tasks import send_email_notification, send_donation_thank_you

# Send welcome email
send_welcome_email.delay(user_id)

# Send story published notification to subscribers
send_story_published_notification.delay(story_id, subscriber_ids)

# Send mentorship request notification
send_mentorship_request_notification.delay(request_id)
```

### Scheduled Tasks

Configured tasks run automatically:
- **Every 5 minutes**: Send pending notifications
- **Daily at 2 AM**: Generate daily analytics report
- **1st of month at 3 AM**: Cleanup old notifications
- **Every 6 hours**: Update recommendation cache
- **Every 15 minutes**: Process moderation queue
- **Mondays at 6 AM**: Generate weekly investor reports

---

## 2. Stripe Payment Integration

### Setup

```bash
# Install Stripe CLI (optional, for testing webhooks)
# https://github.com/stripe/stripe-cli
```

### Configuration

Add to your `.env` file:
```
STRIPE_PUBLIC_KEY=pk_test_YOUR_PUBLIC_KEY
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
```

### API Endpoints

```
POST /api/v1/payments/create_donation_intent/
{
    "amount": 50.00,
    "campaign_id": 123
}

POST /api/v1/payments/confirm_donation/
{
    "payment_intent_id": "pi_...",
    "donation_id": 456
}

POST /api/v1/subscriptions/create_subscription/
{
    "price_id": "price_..."
}

POST /api/v1/subscriptions/cancel_subscription/
{
    "subscription_id": "sub_..."
}
```

### Webhook Setup

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/api/v1/webhooks/stripe/`
3. Select events: 
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
   - `charge.refunded`

### Usage

```python
from funding.stripe_utils import StripePaymentManager

# Create payment intent
intent = StripePaymentManager.create_payment_intent(
    amount=50.00,
    metadata={'user_id': 123}
)

# Create customer
customer = StripePaymentManager.create_customer(
    email='user@example.com',
    name='John Doe'
)

# Create subscription
subscription = StripePaymentManager.create_subscription(
    customer_id=customer.id,
    price_id='price_123'
)
```

---

## 3. Elasticsearch Integration

### Setup

```bash
# Using Docker (recommended)
docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.13.0

# Or install locally
# https://www.elastic.co/downloads/elasticsearch
```

### Configuration

Add to your `.env` file:
```
ELASTICSEARCH_HOST=localhost:9200
SEARCH_BACKEND=elasticsearch
```

### Create Index

```python
from search.elasticsearch_manager import get_elasticsearch_manager

manager = get_elasticsearch_manager()
manager.create_index('stories')
```

### Index Documents

```python
# Bulk index stories
documents = [
    {
        'id': story.id,
        'title': story.title,
        'content': story.content,
        'author': story.author.get_full_name(),
        'category': story.category,
        'created_at': story.created_at,
    }
    for story in Story.objects.all()
]

manager.bulk_index('stories', documents)
```

### API Endpoints

```
GET /api/v1/search/full_text_search/?q=startup+failure
GET /api/v1/search/autocomplete/?q=star&field=title
POST /api/v1/search/advanced_search/
{
    "query": "startup failure",
    "filters": {
        "category": ["technology"],
        "status": "published"
    },
    "page": 1,
    "size": 20
}
GET /api/v1/search/faceted_search/?q=startup&facet=category
```

---

## 4. Recommendation Engine

### Algorithms

- **Hybrid** (default): Combines collaborative + content-based
- **Collaborative**: Based on similar users' preferences
- **Content-based**: Based on story attributes and categories
- **Trending**: Popular stories from recent period
- **Personalized Trending**: Trending in user's preferred categories

### API Endpoints

```
GET /api/v1/recommendations/for_me/?algorithm=hybrid&limit=10
GET /api/v1/recommendations/trending/?days=7&personalized=true
GET /api/v1/recommendations/mentors/?limit=5
POST /api/v1/recommendations/score_story/
{
    "story_id": 123
}
POST /api/v1/recommendations/similar_stories/
{
    "story_id": 123,
    "limit": 10
}
```

### Usage

```python
from search.recommendation_engine import get_recommendations_for_user

# Get personalized recommendations
recommendations = get_recommendations_for_user(
    user=request.user,
    algorithm='hybrid',
    limit=10
)

# Get trending stories
trending = get_recommendations_for_user(
    user=request.user,
    algorithm='trending',
    limit=10
)
```

---

## 5. WebSockets/Real-time Features

### Setup

```bash
# Start with Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8000 myhopestory.asgi:application
```

### Configuration

Redis must be running for Channels:
```
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

### WebSocket Connections

**Notifications:**
```javascript
// Connect to notifications
const socket = new WebSocket('ws://localhost:8000/ws/notifications/');

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'notification') {
        console.log('New notification:', data.message);
    }
};

// Send commands
socket.send(JSON.stringify({
    command: 'mark_read',
    notification_id: 123
}));
```

**Chat:**
```javascript
// Connect to chat
const socket = new WebSocket('ws://localhost:8000/ws/chat/1/');

// Send message
socket.send(JSON.stringify({
    command: 'send_message',
    message: 'Hello!'
}));

// Listen for messages
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'message') {
        console.log(data.username + ': ' + data.message);
    }
};
```

### Production Deployment

For production, use:
- **Gunicorn** for HTTP
- **Daphne** for WebSockets
- **Nginx** as reverse proxy with upstream routing

---

## 6. Analytics Dashboard

### API Endpoints

```
GET /api/v1/analytics/overview/
- User metrics, content metrics, engagement, funding

GET /api/v1/analytics/user_growth/?days=30
- Daily user signup trends

GET /api/v1/analytics/content_analytics/?days=30
- Stories, likes, comments daily metrics
- Top performing stories

GET /api/v1/analytics/funding_analytics/?days=30
- Donation metrics and top campaigns

GET /api/v1/analytics/user_activity/
- Most active users, retention rates

GET /api/v1/analytics/category_insights/
- Stories and engagement by category

GET /api/v1/analytics/user_profile_analytics/
- Personalized analytics for logged-in user
```

### Dashboard Sections

1. **Overview** - Key metrics at a glance
2. **User Growth** - New users trend
3. **Content Metrics** - Stories, engagement over time
4. **Funding** - Donations and campaigns
5. **User Activity** - Active users, retention
6. **Category Insights** - Performance by category
7. **Personal Analytics** - User's own metrics

---

## 7. AI Content Moderation

### Setup

```bash
# Install OpenAI library (in requirements.txt)
pip install openai
```

### Configuration

Add to `.env`:
```
OPENAI_API_KEY=sk-...
MODERATION_ENABLED=true
MODERATION_USE_AI=true
MODERATION_CONFIDENCE_THRESHOLD=0.7
```

### Content Moderation

```python
from moderation.ai_moderation import ContentModerator

# Moderate text
result = ContentModerator.moderate_text(
    content="Your content here",
    use_openai=True  # Falls back to rules if API unavailable
)

# Result structure:
{
    'is_safe': True/False,
    'flags': ['category1', 'category2'],
    'scores': {'category': 0.8},
    'suggestions': []
}
```

### Spam Detection

```python
from moderation.ai_moderation import ContentModerator

spam_analysis = ContentModerator.detect_spam_patterns(
    content="Buy now! Limited offer!",
    user_id=123
)

# Returns spam score (0-1) and indicators
```

### Sentiment Analysis

```python
from moderation.ai_moderation import SentimentAnalyzer

sentiment = SentimentAnalyzer.analyze_sentiment(
    text="This is amazing! I love it."
)

# Returns sentiment and score
```

### Toxicity Detection

```python
from moderation.ai_moderation import ToxicityDetector

toxicity = ToxicityDetector.detect_toxicity(
    text="You're an idiot",
    user_history=None
)

# Returns toxicity score and indicators
```

---

## Environment Variables (.env)

Complete `.env` template:

```env
# Debug
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=myhopestory_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@myhopestory.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis
REDIS_URL=redis://localhost:6379/1

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Elasticsearch
ELASTICSEARCH_HOST=localhost:9200
SEARCH_BACKEND=elasticsearch

# OpenAI
OPENAI_API_KEY=sk-...

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Moderation
MODERATION_ENABLED=True
MODERATION_USE_AI=True
MODERATION_CONFIDENCE_THRESHOLD=0.7
```

---

## Running Everything Locally

### Terminal 1: Django
```bash
python manage.py runserver
```

### Terminal 2: Celery Worker
```bash
celery -A myhopestory worker -l info
```

### Terminal 3: Celery Beat (Scheduler)
```bash
celery -A myhopestory beat -l info
```

### Terminal 4: Daphne (WebSockets)
```bash
daphne -b 0.0.0.0 -p 8001 myhopestory.asgi:application
```

Or use a single command with multiple workers:
```bash
python manage.py runserver & celery -A myhopestory worker -l info & celery -A myhopestory beat -l info
```

---

## Testing Advanced Features

### Test Recommendations
```bash
curl "http://localhost:8000/api/v1/recommendations/for_me/?algorithm=hybrid&limit=5"
```

### Test Analytics
```bash
curl "http://localhost:8000/api/v1/analytics/overview/"
```

### Test Search
```bash
curl "http://localhost:8000/api/v1/search/full_text_search/?q=startup"
```

### Test WebSocket
```javascript
// In browser console
const socket = new WebSocket('ws://localhost:8000/ws/notifications/');
socket.onopen = () => console.log('Connected');
socket.onmessage = (e) => console.log('Message:', e.data);
```

---

## Production Deployment

### Using Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=myhopestory_db
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.13.0
    environment:
      - discovery.type=single-node

  celery:
    build: .
    command: celery -A myhopestory worker -l info
    depends_on:
      - redis

  celery-beat:
    build: .
    command: celery -A myhopestory beat -l info
    depends_on:
      - redis
```

### Deploy with Docker
```bash
docker-compose up -d
```

---

## Troubleshooting

### Celery tasks not running
- Check Redis is running: `redis-cli ping`
- Check worker is running: `ps aux | grep celery`
- Check logs: `tail -f logs/celery.log`

### WebSocket connections failing
- Ensure Daphne is running on correct port
- Check channels_redis is installed: `pip list | grep channels`
- Verify Redis running for channel layer

### Elasticsearch not found
- Start Elasticsearch: `docker run -d -p 9200:9200 elasticsearch:7.13.0`
- Test connection: `curl http://localhost:9200`

### OpenAI API errors
- Verify API key in `.env`
- Check API quota in OpenAI dashboard
- Ensure internet connection for API calls

---

## Next Steps

1. Deploy to production using Docker Compose
2. Set up CI/CD pipeline (GitHub Actions, GitLab CI)
3. Configure monitoring (Sentry, DataDog)
4. Implement additional features:
   - Vector embeddings for semantic search
   - Custom ML models for better recommendations
   - Advanced fraud detection
   - Multi-language support

---

## Support & Documentation

- Django Channels: https://channels.readthedocs.io/
- Celery: https://docs.celeryproject.org/
- Elasticsearch: https://www.elastic.co/guide/
- Stripe API: https://stripe.com/docs/api
- OpenAI: https://platform.openai.com/docs/

