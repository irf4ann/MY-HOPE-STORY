"""
Elasticsearch integration for advanced search functionality.
Provides full-text search, faceted search, and autocomplete.
"""

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ElasticsearchManager:
    """Manages Elasticsearch operations."""
    
    def __init__(self):
        """Initialize Elasticsearch connection."""
        try:
            self.es = Elasticsearch(
                [settings.ELASTICSEARCH_HOST],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            # Test connection
            if not self.es.ping():
                logger.warning("Elasticsearch connection failed")
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch: {e}")
            self.es = None
    
    
    def create_index(self, index_name, body=None):
        """Create an Elasticsearch index."""
        if not self.es:
            logger.warning("Elasticsearch not available")
            return
        
        try:
            if body is None:
                body = {
                    'settings': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0,
                        'analysis': {
                            'analyzer': {
                                'autocomplete': {
                                    'type': 'custom',
                                    'tokenizer': 'standard',
                                    'filter': ['lowercase', 'stop', 'snowball']
                                }
                            }
                        }
                    },
                    'mappings': {
                        'properties': {
                            'title': {
                                'type': 'text',
                                'analyzer': 'standard',
                                'fields': {
                                    'keyword': {'type': 'keyword'},
                                    'autocomplete': {'type': 'text', 'analyzer': 'autocomplete'}
                                }
                            },
                            'content': {
                                'type': 'text',
                                'analyzer': 'standard'
                            },
                            'author': {'type': 'text'},
                            'category': {'type': 'keyword'},
                            'tags': {'type': 'keyword'},
                            'created_at': {'type': 'date'},
                            'views': {'type': 'integer'},
                            'status': {'type': 'keyword'},
                        }
                    }
                }
            
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=body)
                logger.info(f"Index {index_name} created")
            
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
    
    
    def index_document(self, index_name, doc_id, body):
        """Index a single document."""
        if not self.es:
            return
        
        try:
            result = self.es.index(index=index_name, id=doc_id, body=body)
            logger.info(f"Document {doc_id} indexed in {index_name}")
            return result
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
    
    
    def bulk_index(self, index_name, documents):
        """Bulk index documents for better performance."""
        if not self.es:
            return
        
        try:
            actions = []
            for doc in documents:
                action = {
                    "_index": index_name,
                    "_id": doc.get('id'),
                    "_source": doc
                }
                actions.append(action)
            
            success, failed = bulk(self.es, actions, raise_on_error=False)
            logger.info(f"Bulk indexed {success} documents, {failed} failed")
            return success, failed
            
        except Exception as e:
            logger.error(f"Error bulk indexing: {e}")
    
    
    def search(self, index_name, query, size=20, from_=0):
        """Perform a full-text search."""
        if not self.es:
            return []
        
        try:
            search_body = {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': ['title^2', 'content', 'author']
                    }
                },
                'size': size,
                'from': from_
            }
            
            results = self.es.search(index=index_name, body=search_body)
            
            return {
                'total': results['hits']['total']['value'],
                'hits': [hit['_source'] for hit in results['hits']['hits']]
            }
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return {'total': 0, 'hits': []}
    
    
    def autocomplete(self, index_name, prefix, field='title', size=10):
        """Get autocomplete suggestions."""
        if not self.es:
            return []
        
        try:
            search_body = {
                'query': {
                    'match': {
                        f'{field}.autocomplete': {
                            'query': prefix,
                            'fuzziness': 'AUTO'
                        }
                    }
                },
                'size': size
            }
            
            results = self.es.search(index=index_name, body=search_body)
            return [hit['_source'][field] for hit in results['hits']['hits']]
            
        except Exception as e:
            logger.error(f"Error autocompleting: {e}")
            return []
    
    
    def faceted_search(self, index_name, query, facet_field, size=20):
        """Perform faceted search."""
        if not self.es:
            return {'hits': [], 'facets': []}
        
        try:
            search_body = {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': ['title^2', 'content']
                    }
                },
                'aggs': {
                    'facets': {
                        'terms': {
                            'field': facet_field,
                            'size': 100
                        }
                    }
                },
                'size': size
            }
            
            results = self.es.search(index=index_name, body=search_body)
            
            return {
                'hits': [hit['_source'] for hit in results['hits']['hits']],
                'facets': results['aggregations']['facets']['buckets']
            }
            
        except Exception as e:
            logger.error(f"Error in faceted search: {e}")
            return {'hits': [], 'facets': []}
    
    
    def filter_search(self, index_name, query, filters, size=20):
        """Search with additional filters."""
        if not self.es:
            return []
        
        try:
            # Build filter queries
            filter_clauses = []
            for field, values in filters.items():
                if isinstance(values, list):
                    filter_clauses.append({'terms': {field: values}})
                else:
                    filter_clauses.append({'term': {field: values}})
            
            search_body = {
                'query': {
                    'bool': {
                        'must': {
                            'multi_match': {
                                'query': query,
                                'fields': ['title^2', 'content']
                            }
                        },
                        'filter': filter_clauses
                    }
                },
                'size': size
            }
            
            results = self.es.search(index=index_name, body=search_body)
            
            return {
                'total': results['hits']['total']['value'],
                'hits': [hit['_source'] for hit in results['hits']['hits']]
            }
            
        except Exception as e:
            logger.error(f"Error in filter search: {e}")
            return {'total': 0, 'hits': []}
    
    
    def delete_index(self, index_name):
        """Delete an index."""
        if not self.es:
            return
        
        try:
            if self.es.indices.exists(index=index_name):
                self.es.indices.delete(index=index_name)
                logger.info(f"Index {index_name} deleted")
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
    
    
    def get_document(self, index_name, doc_id):
        """Retrieve a document."""
        if not self.es:
            return None
        
        try:
            result = self.es.get(index=index_name, id=doc_id)
            return result['_source']
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return None
    
    
    def delete_document(self, index_name, doc_id):
        """Delete a document."""
        if not self.es:
            return
        
        try:
            self.es.delete(index=index_name, id=doc_id)
            logger.info(f"Document {doc_id} deleted from {index_name}")
        except Exception as e:
            logger.error(f"Error deleting document: {e}")


# Global instance
_es_manager = None


def get_elasticsearch_manager():
    """Get or create Elasticsearch manager instance."""
    global _es_manager
    if _es_manager is None:
        _es_manager = ElasticsearchManager()
    return _es_manager
