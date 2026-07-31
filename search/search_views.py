"""
Advanced search views using Elasticsearch.
Provides full-text search, faceted search, and autocomplete.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from stories.models import Story
from stories.serializers import StorySerializer
from .elasticsearch_manager import get_elasticsearch_manager
import logging

logger = logging.getLogger(__name__)


class AdvancedSearchViewSet(viewsets.ViewSet):
    """
    Advanced search using Elasticsearch.
    Supports full-text search, filtering, faceting, and autocomplete.
    """
    permission_classes = [permissions.AllowAny]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.es_manager = get_elasticsearch_manager()
    
    
    @action(detail=False, methods=['get'])
    def full_text_search(self, request):
        """
        Full-text search across stories.
        
        Query parameters:
        - q: Search query (required)
        - page: Page number (default: 1)
        - size: Results per page (default: 20)
        """
        try:
            query = request.query_params.get('q', '').strip()
            page = int(request.query_params.get('page', 1))
            size = int(request.query_params.get('size', 20))
            
            if not query:
                return Response(
                    {'error': 'Search query required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(query) < 2:
                return Response(
                    {'error': 'Query must be at least 2 characters'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from_index = (page - 1) * size
            
            # Try Elasticsearch first, fallback to database
            if self.es_manager.es:
                results = self.es_manager.search(
                    'stories',
                    query,
                    size=size,
                    from_=from_index
                )
                
                return Response({
                    'count': results['total'],
                    'page': page,
                    'page_size': size,
                    'results': results['hits']
                })
            else:
                # Fallback to database search
                stories = Story.objects.filter(
                    Q(title__icontains=query) |
                    Q(content__icontains=query) |
                    Q(author__first_name__icontains=query) |
                    Q(author__last_name__icontains=query),
                    status='published'
                )[from_index:from_index + size]
                
                return Response({
                    'count': Story.objects.filter(
                        Q(title__icontains=query) |
                        Q(content__icontains=query),
                        status='published'
                    ).count(),
                    'page': page,
                    'page_size': size,
                    'results': StorySerializer(stories, many=True).data
                })
            
        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            return Response(
                {'error': 'Search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """
        Autocomplete suggestions.
        
        Query parameters:
        - q: Search prefix (required)
        - field: Field to search (default: title)
        """
        try:
            prefix = request.query_params.get('q', '').strip()
            field = request.query_params.get('field', 'title')
            
            if not prefix or len(prefix) < 2:
                return Response([])
            
            if self.es_manager.es:
                suggestions = self.es_manager.autocomplete(
                    'stories',
                    prefix,
                    field=field,
                    size=10
                )
                return Response(suggestions)
            else:
                # Fallback to database
                if field == 'title':
                    suggestions = Story.objects.filter(
                        title__icontains=prefix,
                        status='published'
                    ).values_list('title', flat=True).distinct()[:10]
                elif field == 'author':
                    suggestions = Story.objects.filter(
                        author__first_name__icontains=prefix,
                        status='published'
                    ).values_list('author__first_name', flat=True).distinct()[:10]
                else:
                    suggestions = []
                
                return Response(list(suggestions))
            
        except Exception as e:
            logger.error(f"Error in autocomplete: {e}")
            return Response([], status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    @action(detail=False, methods=['get'])
    def faceted_search(self, request):
        """
        Faceted search with aggregations.
        
        Query parameters:
        - q: Search query (required)
        - facet: Field to facet on (default: category)
        """
        try:
            query = request.query_params.get('q', '').strip()
            facet_field = request.query_params.get('facet', 'category')
            
            if not query:
                return Response(
                    {'error': 'Search query required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if self.es_manager.es:
                results = self.es_manager.faceted_search(
                    'stories',
                    query,
                    facet_field=facet_field
                )
                
                return Response({
                    'hits': results['hits'],
                    'facets': results['facets']
                })
            else:
                # Fallback to database
                stories = Story.objects.filter(
                    Q(title__icontains=query) |
                    Q(content__icontains=query),
                    status='published'
                )
                
                facets = stories.values(facet_field).annotate(
                    count=Count('id')
                ).order_by('-count')
                
                return Response({
                    'hits': StorySerializer(stories[:20], many=True).data,
                    'facets': list(facets)
                })
            
        except Exception as e:
            logger.error(f"Error in faceted search: {e}")
            return Response(
                {'error': 'Faceted search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'])
    def advanced_search(self, request):
        """
        Advanced search with multiple filters.
        
        Request body:
        {
            "query": "failure lessons",
            "filters": {
                "category": ["technology", "startup"],
                "status": "published"
            },
            "page": 1,
            "size": 20
        }
        """
        try:
            query = request.data.get('query', '').strip()
            filters = request.data.get('filters', {})
            page = int(request.data.get('page', 1))
            size = int(request.data.get('size', 20))
            
            if not query:
                return Response(
                    {'error': 'Search query required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from_index = (page - 1) * size
            
            if self.es_manager.es:
                # Add status filter
                filters['status'] = 'published'
                
                results = self.es_manager.filter_search(
                    'stories',
                    query,
                    filters=filters,
                    size=size
                )
                
                return Response({
                    'count': results['total'],
                    'page': page,
                    'page_size': size,
                    'results': results['hits']
                })
            else:
                # Fallback to database
                stories = Story.objects.filter(
                    Q(title__icontains=query) |
                    Q(content__icontains=query),
                    status='published'
                )
                
                # Apply additional filters
                for field, value in filters.items():
                    if field != 'status':
                        if isinstance(value, list):
                            stories = stories.filter(**{f'{field}__in': value})
                        else:
                            stories = stories.filter(**{field: value})
                
                total_count = stories.count()
                stories = stories[from_index:from_index + size]
                
                return Response({
                    'count': total_count,
                    'page': page,
                    'page_size': size,
                    'results': StorySerializer(stories, many=True).data
                })
            
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return Response(
                {'error': 'Advanced search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
