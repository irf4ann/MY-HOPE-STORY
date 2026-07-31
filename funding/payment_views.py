"""
Payment API views for handling donations and subscriptions.
Integrates with Stripe for secure payment processing.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import stripe
import json
import logging

from django.conf import settings
from .stripe_utils import StripePaymentManager
from .models import Donation
from .serializers import DonationSerializer

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentIntentViewSet(viewsets.ViewSet):
    """
    Create and manage payment intents for donations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_donation_intent(self, request):
        """Create a payment intent for a donation."""
        try:
            amount = request.data.get('amount')
            campaign_id = request.data.get('campaign_id')
            
            if not amount or not campaign_id:
                return Response(
                    {'error': 'Amount and campaign_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate amount
            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid amount'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create donation record (pending)
            donation = Donation.objects.create(
                donor=request.user,
                campaign_id=campaign_id,
                amount=amount,
                status='pending',
            )
            
            # Create payment intent
            intent = StripePaymentManager.create_payment_intent(
                amount=amount,
                metadata={
                    'donation_id': donation.id,
                    'user_id': request.user.id,
                    'campaign_id': campaign_id,
                }
            )
            
            return Response({
                'client_secret': intent.client_secret,
                'donation_id': donation.id,
                'payment_intent_id': intent.id,
            })
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'])
    def confirm_donation(self, request):
        """Confirm a donation after payment."""
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            donation_id = request.data.get('donation_id')
            
            if not payment_intent_id or not donation_id:
                return Response(
                    {'error': 'payment_intent_id and donation_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify payment intent
            intent = StripePaymentManager.retrieve_payment_intent(payment_intent_id)
            
            if intent.status != 'succeeded':
                return Response(
                    {'error': 'Payment not completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update donation
            donation = Donation.objects.get(id=donation_id)
            donation.status = 'completed'
            donation.stripe_payment_intent = payment_intent_id
            donation.payment_date = timezone.now()
            donation.save()
            
            # Trigger thank you email
            from notifications.tasks import send_donation_thank_you
            send_donation_thank_you.delay(donation.id)
            
            return Response(DonationSerializer(donation).data)
            
        except Exception as e:
            logger.error(f"Error confirming donation: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionViewSet(viewsets.ViewSet):
    """
    Manage subscriptions (for premium features, memberships, etc).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        """Create a subscription."""
        try:
            price_id = request.data.get('price_id')
            
            if not price_id:
                return Response(
                    {'error': 'price_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create Stripe customer
            if hasattr(request.user, 'stripe_customer_id') and request.user.stripe_customer_id:
                customer_id = request.user.stripe_customer_id
            else:
                customer = StripePaymentManager.create_customer(
                    email=request.user.email,
                    name=request.user.get_full_name(),
                    metadata={'user_id': request.user.id}
                )
                customer_id = customer.id
                # Save to user profile if you have that field
            
            # Create subscription
            subscription = StripePaymentManager.create_subscription(
                customer_id=customer_id,
                price_id=price_id,
                metadata={'user_id': request.user.id}
            )
            
            return Response({
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
            })
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'])
    def cancel_subscription(self, request):
        """Cancel a subscription."""
        try:
            subscription_id = request.data.get('subscription_id')
            
            if not subscription_id:
                return Response(
                    {'error': 'subscription_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subscription = StripePaymentManager.cancel_subscription(subscription_id)
            
            return Response({
                'subscription_id': subscription.id,
                'status': subscription.status,
            })
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    Validates webhook signature and processes events.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Process event
        from .stripe_utils import StripePaymentManager
        StripePaymentManager.handle_webhook(event)
        
        return JsonResponse({'status': 'success'})
        
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid Stripe webhook signature")
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JsonResponse({'error': str(e)}, status=400)
