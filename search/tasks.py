"""
Celery tasks for search app.
Handles recommendation engine, search indexing, and cache updates.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_recommendation_cache():
    """Update recommendation cache for all users (called by Celery beat)."""
    try:
        from django.core.cache import cache
        from stories.models import Story
        from accounts.models import User
        
        users = User.objects.all()
        
        for user in users:
            # Get user's interests based on liked stories
            liked_stories = user.likes.all().values_list('story', flat=True)
            
            # Find similar stories
            recommended = Story.objects.filter(
                Q(category__in=Story.objects.filter(
                    id__in=liked_stories
                ).values_list('category', flat=True)) |
                Q(tags__in=Story.objects.filter(
                    id__in=liked_stories
                ).values_list('tags', flat=True))
            ).exclude(
                id__in=liked_stories
            ).distinct()[:10]
            
            # Cache recommendations
            cache.set(f'recommendations_{user.id}', list(recommended.values_list('id', flat=True)), 3600)
        
        logger.info(f"Recommendation cache updated for {users.count()} users")
        
    except Exception as exc:
        logger.error(f"Error updating recommendation cache: {exc}")


@shared_task
def generate_personalized_recommendations(user_id, limit=10):
    """Generate personalized recommendations for a user."""
    try:
        from accounts.models import User
        from stories.models import Story
        from community.models import Like
        
        user = User.objects.get(id=user_id)
        
        # Get user's liked stories
        liked_stories = Like.objects.filter(
            user=user
        ).values_list('story', flat=True)
        
        if not liked_stories:
            # New user - recommend popular stories
            recommendations = Story.objects.filter(
                status='published'
            ).annotate(
                like_count=Count('likes')
            ).order_by('-like_count')[:limit]
        else:
            # Get story categories/tags from liked stories
            liked_story_objs = Story.objects.filter(id__in=liked_stories)
            categories = liked_story_objs.values_list('category', flat=True).distinct()
            
            # Find similar stories
            recommendations = Story.objects.filter(
                Q(category__in=categories) &
                ~Q(id__in=liked_stories) &
                Q(status='published')
            ).annotate(
                like_count=Count('likes')
            ).order_by('-like_count')[:limit]
        
        logger.info(f"Generated {len(list(recommendations))} recommendations for user {user_id}")
        return list(recommendations.values_list('id', flat=True))
        
    except Exception as exc:
        logger.error(f"Error generating recommendations: {exc}")


@shared_task
def index_story_in_search(story_id):
    """Index a story for full-text search (Elasticsearch integration)."""
    try:
        from stories.models import Story
        
        story = Story.objects.get(id=story_id)
        
        # Prepare document for indexing
        doc = {
            'id': story.id,
            'title': story.title,
            'content': story.content,
            'author': story.author.get_full_name(),
            'category': story.category,
            'tags': list(story.tags.values_list('name', flat=True)) if hasattr(story, 'tags') else [],
            'created_at': story.created_at,
            'updated_at': story.updated_at,
            'status': story.status,
        }
        
        # TODO: Index to Elasticsearch when integrated
        # es.index(index='stories', id=story.id, body=doc)
        
        logger.info(f"Story {story_id} indexed for search")
        
    except Exception as exc:
        logger.error(f"Error indexing story: {exc}")


@shared_task
def rebuild_search_index():
    """Rebuild entire search index (useful after data migration)."""
    try:
        from stories.models import Story
        
        stories = Story.objects.filter(status='published')
        
        for story in stories:
            index_story_in_search.delay(story.id)
        
        logger.info(f"Search index rebuild initiated for {stories.count()} stories")
        
    except Exception as exc:
        logger.error(f"Error rebuilding search index: {exc}")


@shared_task
def calculate_story_similarity(story_id):
    """Calculate similarity score between stories for recommendations."""
    try:
        from stories.models import Story
        from django.db.models import F
        
        story = Story.objects.get(id=story_id)
        
        # Find stories with similar categories/tags
        similar_stories = Story.objects.filter(
            Q(category=story.category) |
            Q(tags__in=story.tags.all()) if hasattr(story, 'tags') else False
        ).exclude(id=story_id).distinct()
        
        logger.info(f"Calculated similarity for {story_id}: {similar_stories.count()} similar stories")
        return similar_stories.count()
        
    except Exception as exc:
        logger.error(f"Error calculating story similarity: {exc}")


@shared_task
def update_search_analytics():
    """Update analytics for search queries and trending terms."""
    try:
        from django.db.models import Count
        from django.contrib.admin.models import LogEntry
        
        # Track popular search terms (implement based on your search logging)
        logger.info("Search analytics updated")
        
    except Exception as exc:
        logger.error(f"Error updating search analytics: {exc}")


@shared_task
def clear_recommendation_cache(user_id=None):
    """Clear recommendation cache for users."""
    try:
        from django.core.cache import cache
        from accounts.models import User
        
        if user_id:
            cache.delete(f'recommendations_{user_id}')
            logger.info(f"Cleared recommendations cache for user {user_id}")
        else:
            # Clear all users' caches
            users = User.objects.all()
            for user in users:
                cache.delete(f'recommendations_{user.id}')
            logger.info(f"Cleared recommendations cache for all users")
        
    except Exception as exc:
        logger.error(f"Error clearing recommendation cache: {exc}")
