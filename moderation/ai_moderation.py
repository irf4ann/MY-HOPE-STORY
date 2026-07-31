"""
AI-powered content moderation system.
Integrates with OpenAI API and implements custom NLP-based moderation.
"""

import openai
from django.conf import settings
from django.utils import timezone
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Initialize OpenAI
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY


class ContentModerator:
    """AI-powered content moderation system."""
    
    # Offensive keywords database
    BANNED_KEYWORDS = {
        'hate_speech': ['slur1', 'slur2'],  # Add real keywords
        'violence': ['kill', 'destroy', 'bomb'],
        'spam': ['click here', 'limited time', 'act now'],
        'harassment': ['idiot', 'stupid', 'loser'],
    }
    
    URLS_REGEX = re.compile(r'https?://[^\s]+')
    SUSPICIOUS_PATTERNS = re.compile(r'(\w)\1{4,}|[A-Z]{5,}')  # Repeated chars, all caps
    
    @staticmethod
    def moderate_text(content, use_openai=True):
        """
        Moderate text content using AI.
        Returns moderation result with scores and flags.
        """
        try:
            result = {
                'is_safe': True,
                'flags': [],
                'scores': {},
                'suggestions': [],
            }
            
            if not content:
                return result
            
            # Use OpenAI API if available and enabled
            if use_openai and settings.OPENAI_API_KEY:
                result.update(ContentModerator._moderate_with_openai(content))
            else:
                result.update(ContentModerator._moderate_with_rules(content))
            
            return result
            
        except Exception as e:
            logger.error(f"Error moderating content: {e}")
            return {
                'is_safe': True,  # Default to allowing if moderation fails
                'flags': [],
                'scores': {},
                'error': str(e)
            }
    
    
    @staticmethod
    def _moderate_with_openai(content):
        """Moderate using OpenAI's moderation API."""
        try:
            response = openai.Moderation.create(input=content)
            
            result = response['results'][0]
            
            return {
                'is_safe': not result['flagged'],
                'flags': [category for category, flagged in result['categories'].items() if flagged],
                'scores': result['category_scores'],
                'using_openai': True,
            }
            
        except Exception as e:
            logger.error(f"Error with OpenAI moderation: {e}")
            # Fallback to rule-based moderation
            return ContentModerator._moderate_with_rules(content)
    
    
    @staticmethod
    def _moderate_with_rules(content):
        """Moderate using rule-based approach."""
        flags = []
        scores = defaultdict(float)
        
        content_lower = content.lower()
        
        # Check for banned keywords
        for category, keywords in ContentModerator.BANNED_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    flags.append(category)
                    scores[category] = min(1.0, scores[category] + 0.3)
        
        # Check for suspicious URLs
        urls = ContentModerator.URLS_REGEX.findall(content)
        if len(urls) > 3:
            flags.append('spam')
            scores['spam'] = min(1.0, scores['spam'] + 0.2)
        
        # Check for suspicious patterns (repeated characters, ALL CAPS)
        if ContentModerator.SUSPICIOUS_PATTERNS.search(content):
            flags.append('suspicious')
            scores['suspicious'] = min(1.0, scores['suspicious'] + 0.1)
        
        # Length check
        if len(content) > 10000:
            logger.warning("Content exceeds 10000 characters")
            scores['length'] = 0.5
        
        return {
            'is_safe': len(flags) == 0,
            'flags': list(set(flags)),
            'scores': dict(scores),
            'using_openai': False,
        }
    
    
    @staticmethod
    def moderate_image(image_url, use_vision_api=True):
        """
        Moderate image using vision API.
        Can detect inappropriate content, violence, etc.
        """
        try:
            if use_vision_api and settings.OPENAI_API_KEY:
                # Use OpenAI's vision API
                response = openai.ChatCompletion.create(
                    model="gpt-4-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Is this image appropriate for a professional platform? Check for violence, inappropriate content, or spam. Reply with YES or NO and a brief reason."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }],
                    max_tokens=100
                )
                
                content = response['choices'][0]['message']['content'].lower()
                is_safe = 'yes' in content
                
                return {
                    'is_safe': is_safe,
                    'assessment': content,
                    'using_vision_api': True,
                }
            else:
                return {
                    'is_safe': True,  # Can't moderate without API
                    'assessment': 'No vision API configured',
                    'using_vision_api': False,
                }
        
        except Exception as e:
            logger.error(f"Error moderating image: {e}")
            return {
                'is_safe': True,
                'error': str(e),
            }
    
    
    @staticmethod
    def detect_spam_patterns(content, user_id=None):
        """Detect spam patterns in content."""
        spam_score = 0
        spam_indicators = []
        
        content_lower = content.lower()
        
        # Check for promotional content
        promo_keywords = ['buy now', 'click here', 'limited offer', 'special deal', 'free money']
        promo_count = sum(1 for kw in promo_keywords if kw in content_lower)
        if promo_count > 0:
            spam_score += promo_count * 0.2
            spam_indicators.append('promotional_content')
        
        # Check for repetitive posts
        if user_id:
            from stories.models import Story
            similar_stories = Story.objects.filter(
                author_id=user_id,
                content__icontains=content[:50]  # First 50 chars
            ).count()
            
            if similar_stories > 3:
                spam_score += 0.3
                spam_indicators.append('repetitive_posting')
        
        # Check for excessive links
        link_count = len(ContentModerator.URLS_REGEX.findall(content))
        if link_count > 5:
            spam_score += 0.3
            spam_indicators.append('excessive_links')
        
        # Check for all caps
        if len(content) > 10 and sum(1 for c in content if c.isupper()) / len(content) > 0.5:
            spam_score += 0.2
            spam_indicators.append('excessive_caps')
        
        return {
            'is_spam': spam_score > 0.5,
            'spam_score': min(1.0, spam_score),
            'indicators': spam_indicators,
        }
    
    
    @staticmethod
    def generate_moderation_report(content_id, content_type, moderation_result):
        """Generate a detailed moderation report."""
        from moderation.models import ContentFlag
        
        try:
            flag = ContentFlag.objects.create(
                content_id=content_id,
                content_type=content_type,
                reason=','.join(moderation_result.get('flags', [])),
                confidence_score=max(moderation_result.get('scores', {}).values()) if moderation_result.get('scores') else 0,
                status='pending' if not moderation_result.get('is_safe') else 'approved',
                moderation_data=str(moderation_result)
            )
            
            logger.info(f"Moderation report created for {content_type} {content_id}")
            return flag
            
        except Exception as e:
            logger.error(f"Error creating moderation report: {e}")
            return None


class SentimentAnalyzer:
    """Analyze sentiment of content."""
    
    @staticmethod
    def analyze_sentiment(text):
        """
        Analyze sentiment using OpenAI.
        Returns sentiment (positive, negative, neutral) and score.
        """
        try:
            if settings.OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "user",
                        "content": f"Analyze the sentiment of this text. Reply with POSITIVE, NEGATIVE, or NEUTRAL followed by a score from -1 to 1.\n\nText: {text}"
                    }],
                    temperature=0,
                    max_tokens=50
                )
                
                content = response['choices'][0]['message']['content']
                
                # Parse response
                if 'positive' in content.lower():
                    sentiment = 'positive'
                elif 'negative' in content.lower():
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                # Extract score
                try:
                    score_str = ''.join(c for c in content if c.isdigit() or c == '.' or c == '-')
                    score = float(score_str) if score_str else 0
                except:
                    score = 0
                
                return {
                    'sentiment': sentiment,
                    'score': score,
                    'full_response': content,
                }
            else:
                # Simple fallback
                text_lower = text.lower()
                negative_words = ['bad', 'worse', 'hate', 'terrible', 'awful']
                positive_words = ['great', 'love', 'excellent', 'amazing', 'wonderful']
                
                neg_count = sum(1 for w in negative_words if w in text_lower)
                pos_count = sum(1 for w in positive_words if w in text_lower)
                
                if pos_count > neg_count:
                    sentiment = 'positive'
                elif neg_count > pos_count:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                return {
                    'sentiment': sentiment,
                    'score': (pos_count - neg_count) / max(1, pos_count + neg_count),
                }
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'unknown',
                'score': 0,
                'error': str(e)
            }


class ToxicityDetector:
    """Detect toxic behavior and patterns."""
    
    @staticmethod
    def detect_toxicity(text, user_history=None):
        """Detect toxic language and behavior."""
        toxicity_score = 0
        toxic_indicators = []
        
        text_lower = text.lower()
        
        # Profanity/insults
        insult_keywords = ['stupid', 'idiot', 'dumb', 'moron']
        if any(kw in text_lower for kw in insult_keywords):
            toxicity_score += 0.4
            toxic_indicators.append('insults')
        
        # Harassment patterns
        harassment_indicators = [
            (r'you (suck|are awful|are terrible)', 'targeted_attack'),
            (r'(everyone hates|nobody likes)', 'grouping'),
        ]
        
        for pattern, indicator in harassment_indicators:
            if re.search(pattern, text_lower):
                toxicity_score += 0.3
                toxic_indicators.append(indicator)
        
        # Check user history for patterns
        if user_history:
            recent_violations = user_history.get('violations_last_week', 0)
            if recent_violations > 2:
                toxicity_score += 0.2
                toxic_indicators.append('repeat_offender')
        
        return {
            'is_toxic': toxicity_score > 0.5,
            'toxicity_score': min(1.0, toxicity_score),
            'indicators': toxic_indicators,
        }
