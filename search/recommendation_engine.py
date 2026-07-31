"""
Advanced recommendation engine using multiple algorithms.
Implements collaborative filtering, content-based, and hybrid recommendations.
"""

from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Advanced recommendation engine with multiple algorithms."""
    
    @staticmethod
    def get_collaborative_recommendations(user, limit=10):
        """
        Collaborative filtering based on user interactions.
        Finds similar users and recommends what they liked.
        """
        try:
            from accounts.models import User
            from stories.models import Story
            from community.models import Like
            
            # Get user's liked stories
            user_likes = Like.objects.filter(user=user).values_list('story_id', flat=True)
            
            if not user_likes:
                # New user - return popular stories
                return Story.objects.filter(
                    status='published'
                ).annotate(
                    like_count=Count('likes')
                ).order_by('-like_count')[:limit]
            
            # Find similar users (who liked same stories)
            similar_users = User.objects.filter(
                likes__story_id__in=user_likes
            ).exclude(id=user.id).annotate(
                similarity=Count('likes')
            ).order_by('-similarity')[:5]
            
            # Get stories liked by similar users but not by current user
            recommendations = Story.objects.filter(
                likes__user__in=similar_users,
                status='published'
            ).exclude(
                id__in=user_likes
            ).annotate(
                like_count=Count('likes')
            ).order_by('-like_count').distinct()[:limit]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {e}")
            return Story.objects.none()
    
    
    @staticmethod
    def get_content_based_recommendations(user, limit=10):
        """
        Content-based filtering based on story attributes.
        Recommends stories similar to what user has liked.
        """
        try:
            from stories.models import Story
            from community.models import Like
            
            # Get user's liked stories
            user_likes = Like.objects.filter(user=user).values_list('story_id', flat=True)
            
            if not user_likes:
                return Story.objects.none()
            
            # Get attributes of liked stories
            liked_stories = Story.objects.filter(id__in=user_likes)
            
            # Build preference profile
            category_prefs = defaultdict(int)
            tag_prefs = defaultdict(int)
            author_prefs = defaultdict(int)
            
            for story in liked_stories:
                category_prefs[story.category] += 1
                author_prefs[story.author_id] += 1
                if hasattr(story, 'tags'):
                    for tag in story.tags.all():
                        tag_prefs[tag.id] += 1
            
            # Find stories matching user preferences
            recommendations = Story.objects.filter(
                Q(category__in=[k for k, v in sorted(category_prefs.items(), key=lambda x: x[1], reverse=True)[:3]]) |
                Q(author_id__in=[k for k, v in sorted(author_prefs.items(), key=lambda x: x[1], reverse=True)[:2]]),
                status='published'
            ).exclude(
                id__in=user_likes
            ).annotate(
                like_count=Count('likes')
            ).order_by('-like_count')[:limit]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in content-based filtering: {e}")
            return Story.objects.none()
    
    
    @staticmethod
    def get_hybrid_recommendations(user, limit=10):
        """
        Hybrid approach combining multiple algorithms.
        Uses both collaborative and content-based recommendations.
        """
        try:
            collab = list(RecommendationEngine.get_collaborative_recommendations(user, limit=int(limit/2)))
            content = list(RecommendationEngine.get_content_based_recommendations(user, limit=int(limit/2)))
            
            # Combine and deduplicate
            recommendations = []
            seen_ids = set()
            
            for story in collab + content:
                if story.id not in seen_ids:
                    recommendations.append(story)
                    seen_ids.add(story.id)
                    if len(recommendations) >= limit:
                        break
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in hybrid recommendations: {e}")
            return []
    
    
    @staticmethod
    def get_trending_recommendations(limit=10, days=7):
        """
        Get trending stories based on recent engagement.
        """
        try:
            from stories.models import Story
            from community.models import Like
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            trending = Story.objects.filter(
                status='published',
                created_at__gte=cutoff_date
            ).annotate(
                recent_likes=Count(
                    'likes',
                    filter=Q(likes__created_at__gte=cutoff_date)
                ),
                total_likes=Count('likes')
            ).order_by('-recent_likes', '-total_likes')[:limit]
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting trending stories: {e}")
            return Story.objects.none()
    
    
    @staticmethod
    def get_personalized_trending(user, limit=10, days=7):
        """
        Get trending stories in user's preferred categories.
        """
        try:
            from stories.models import Story
            from community.models import Like
            
            # Get user's category preferences
            liked_stories = Like.objects.filter(
                user=user
            ).values_list('story__category', flat=True)
            
            if not liked_stories:
                return RecommendationEngine.get_trending_recommendations(limit, days)
            
            # Get trending in preferred categories
            cutoff_date = timezone.now() - timedelta(days=days)
            
            trending = Story.objects.filter(
                status='published',
                category__in=liked_stories,
                created_at__gte=cutoff_date
            ).annotate(
                recent_likes=Count(
                    'likes',
                    filter=Q(likes__created_at__gte=cutoff_date)
                )
            ).order_by('-recent_likes')[:limit]
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting personalized trending: {e}")
            return Story.objects.none()
    
    
    @staticmethod
    def get_mentor_recommendations(user, limit=5):
        """
        Recommend mentors based on user's industry/expertise.
        """
        try:
            from accounts.models import User
            from mentorship.models import MentorProfile
            
            # Get user's interests/industry
            # This assumes you have profile fields for this
            
            mentors = User.objects.filter(
                mentorprofile__is_active=True,
            ).exclude(
                id=user.id
            ).annotate(
                rating=Avg('mentorprofile__reviews__rating'),
                session_count=Count('mentorprofile__sessions')
            ).order_by('-rating', '-session_count')[:limit]
            
            return mentors
            
        except Exception as e:
            logger.error(f"Error getting mentor recommendations: {e}")
            return User.objects.none()
    
    
    @staticmethod
    def get_investor_recommendations(campaign, limit=10):
        """
        Recommend potential investors for a campaign.
        Based on their investment history and preferences.
        """
        try:
            from investors.models import Investor, Investment
            from stories.models import Story
            
            # Get similar campaigns investor has funded
            similar_campaigns = Campaign.objects.filter(
                category=campaign.category
            ).exclude(id=campaign.id)
            
            investors = Investor.objects.filter(
                investments__campaign__in=similar_campaigns
            ).annotate(
                investment_count=Count('investments'),
                avg_investment=Avg('investments__amount')
            ).order_by('-investment_count', '-avg_investment')[:limit]
            
            return investors
            
        except Exception as e:
            logger.error(f"Error getting investor recommendations: {e}")
            return []
    
    
    @staticmethod
    def calculate_recommendation_score(user, story):
        """
        Calculate a recommendation score for a story (0-100).
        Based on multiple factors.
        """
        try:
            from community.models import Like, Comment, Bookmark
            
            score = 0
            
            # Factor 1: Engagement with similar stories (20 points)
            similar_stories = Story.objects.filter(
                category=story.category
            ).exclude(id=story.id)
            
            user_engagement = Like.objects.filter(
                user=user,
                story__in=similar_stories
            ).count()
            
            if user_engagement > 0:
                score += min(20, user_engagement * 2)
            
            # Factor 2: Story quality (30 points)
            like_count = Like.objects.filter(story=story).count()
            comment_count = Comment.objects.filter(story=story).count()
            view_count = story.views_count
            
            quality_score = min(30, (like_count * 2 + comment_count + view_count / 10))
            score += quality_score
            
            # Factor 3: Recency (15 points)
            days_old = (timezone.now() - story.created_at).days
            if days_old <= 7:
                score += 15
            elif days_old <= 30:
                score += 10
            elif days_old <= 90:
                score += 5
            
            # Factor 4: Author credibility (15 points)
            author_likes = Like.objects.filter(
                story__author=story.author
            ).count()
            
            author_followers = story.author.followers.count() if hasattr(story.author, 'followers') else 0
            credibility = min(15, (author_followers + author_likes / 5))
            score += credibility
            
            # Factor 5: User's bookmark history (10 points)
            bookmarked = Bookmark.objects.filter(
                user=user,
                story__category=story.category
            ).count()
            
            if bookmarked > 0:
                score += 10
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Error calculating recommendation score: {e}")
            return 0
    
    
    @staticmethod
    def cache_recommendations(user_id, recommendations, ttl=3600):
        """Cache recommendations for faster retrieval."""
        try:
            cache_key = f'recommendations_{user_id}'
            rec_ids = [r.id for r in recommendations]
            cache.set(cache_key, rec_ids, ttl)
            logger.info(f"Cached {len(rec_ids)} recommendations for user {user_id}")
        except Exception as e:
            logger.error(f"Error caching recommendations: {e}")
    
    
    @staticmethod
    def get_cached_recommendations(user_id, limit=10):
        """Get recommendations from cache if available."""
        try:
            cache_key = f'recommendations_{user_id}'
            rec_ids = cache.get(cache_key)
            
            if rec_ids:
                from stories.models import Story
                return Story.objects.filter(id__in=rec_ids[:limit])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached recommendations: {e}")
            return None


# Convenience functions
def get_recommendations_for_user(user, algorithm='hybrid', limit=10):
    """Get recommendations using specified algorithm."""
    if algorithm == 'collaborative':
        return RecommendationEngine.get_collaborative_recommendations(user, limit)
    elif algorithm == 'content':
        return RecommendationEngine.get_content_based_recommendations(user, limit)
    elif algorithm == 'trending':
        return RecommendationEngine.get_trending_recommendations(limit)
    elif algorithm == 'personalized_trending':
        return RecommendationEngine.get_personalized_trending(user, limit)
    else:  # hybrid
        return RecommendationEngine.get_hybrid_recommendations(user, limit)
