"""
API views for recommendations using the recommendation engine.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from stories.models import Story
from stories.serializers import StorySerializer
from .recommendation_engine import RecommendationEngine, get_recommendations_for_user
import logging

logger = logging.getLogger(__name__)


class RecommendationViewSet(viewsets.ViewSet):
    """
    Recommendations API using advanced recommendation engine.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def for_me(self, request):
        """
        Get personalized recommendations for logged-in user.
        
        Query parameters:
        - algorithm: hybrid|collaborative|content|trending|personalized_trending (default: hybrid)
        - limit: Number of recommendations (default: 10, max: 50)
        """
        try:
            algorithm = request.query_params.get('algorithm', 'hybrid')
            limit = min(int(request.query_params.get('limit', 10)), 50)
            
            # Validate algorithm
            valid_algorithms = ['hybrid', 'collaborative', 'content', 'trending', 'personalized_trending']
            if algorithm not in valid_algorithms:
                return Response(
                    {'error': f'Invalid algorithm. Must be one of: {", ".join(valid_algorithms)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get recommendations
            recommendations = get_recommendations_for_user(request.user, algorithm=algorithm, limit=limit)
            
            return Response({
                'algorithm': algorithm,
                'count': len(list(recommendations)),
                'results': StorySerializer(recommendations, many=True).data
            })
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return Response(
                {'error': 'Failed to generate recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending stories.
        
        Query parameters:
        - days: Number of days to consider (default: 7)
        - limit: Number of results (default: 10)
        - personalized: Include user preferences (default: false)
        """
        try:
            days = int(request.query_params.get('days', 7))
            limit = min(int(request.query_params.get('limit', 10)), 50)
            personalized = request.query_params.get('personalized', 'false').lower() == 'true'
            
            if personalized and request.user.is_authenticated:
                trending = RecommendationEngine.get_personalized_trending(request.user, limit, days)
            else:
                trending = RecommendationEngine.get_trending_recommendations(limit, days)
            
            return Response({
                'personalized': personalized and request.user.is_authenticated,
                'days': days,
                'count': len(list(trending)),
                'results': StorySerializer(trending, many=True).data
            })
            
        except Exception as e:
            logger.error(f"Error getting trending stories: {e}")
            return Response(
                {'error': 'Failed to get trending stories'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def mentors(self, request):
        """
        Get recommended mentors.
        
        Query parameters:
        - limit: Number of results (default: 5)
        """
        try:
            limit = min(int(request.query_params.get('limit', 5)), 20)
            
            mentors = RecommendationEngine.get_mentor_recommendations(request.user, limit)
            
            from accounts.serializers import UserSerializer
            return Response({
                'count': len(list(mentors)),
                'results': UserSerializer(mentors, many=True).data
            })
            
        except Exception as e:
            logger.error(f"Error getting mentor recommendations: {e}")
            return Response(
                {'error': 'Failed to get mentor recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'])
    def score_story(self, request):
        """
        Calculate recommendation score for a story.
        
        Request body:
        {
            "story_id": 123
        }
        """
        try:
            story_id = request.data.get('story_id')
            
            if not story_id:
                return Response(
                    {'error': 'story_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            story = Story.objects.get(id=story_id)
            score = RecommendationEngine.calculate_recommendation_score(request.user, story)
            
            return Response({
                'story_id': story_id,
                'score': score,
                'likely_to_like': score > 60
            })
            
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error scoring story: {e}")
            return Response(
                {'error': 'Failed to calculate score'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'])
    def similar_stories(self, request):
        """
        Get stories similar to a given story.
        
        Request body:
        {
            "story_id": 123,
            "limit": 10
        }
        """
        try:
            story_id = request.data.get('story_id')
            limit = min(int(request.data.get('limit', 10)), 50)
            
            if not story_id:
                return Response(
                    {'error': 'story_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            story = Story.objects.get(id=story_id)
            
            # Find similar stories by category and tags
            similar = Story.objects.filter(
                category=story.category,
                status='published'
            ).exclude(id=story_id).annotate(
                models.Count('likes')
            ).order_by('-likes__count')[:limit]
            
            return Response({
                'source_story_id': story_id,
                'count': len(list(similar)),
                'results': StorySerializer(similar, many=True).data
            })
            
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting similar stories: {e}")
            return Response(
                {'error': 'Failed to get similar stories'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
