"""
Stripe payment utilities and integration.
Handles payment processing, refunds, and subscription management.
"""

import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentManager:
    """Manages Stripe payment operations."""
    
    @staticmethod
    def create_payment_intent(amount, currency='usd', metadata=None):
        """Create a Stripe payment intent."""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(Decimal(amount) * 100),  # Convert to cents
                currency=currency,
                metadata=metadata or {},
            )
            logger.info(f"Payment intent created: {intent.id}")
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise


    @staticmethod
    def confirm_payment_intent(intent_id):
        """Confirm a payment intent."""
        try:
            intent = stripe.PaymentIntent.retrieve(intent_id)
            logger.info(f"Payment intent confirmed: {intent.id}")
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming intent: {e}")
            raise


    @staticmethod
    def create_customer(email, name=None, metadata=None):
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            logger.info(f"Stripe customer created: {customer.id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise


    @staticmethod
    def create_subscription(customer_id, price_id, metadata=None):
        """Create a subscription."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                metadata=metadata or {},
            )
            logger.info(f"Subscription created: {subscription.id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise


    @staticmethod
    def cancel_subscription(subscription_id, at_period_end=True):
        """Cancel a subscription."""
        try:
            subscription = stripe.Subscription.delete(
                subscription_id,
                invoice_settings={
                    'custom_fields': None
                } if not at_period_end else None
            )
            logger.info(f"Subscription cancelled: {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            raise


    @staticmethod
    def refund_payment(payment_intent_id, amount=None):
        """Refund a payment."""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=int(Decimal(amount) * 100) if amount else None,
            )
            logger.info(f"Refund created: {refund.id}")
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            raise


    @staticmethod
    def retrieve_payment_intent(intent_id):
        """Retrieve payment intent details."""
        try:
            intent = stripe.PaymentIntent.retrieve(intent_id)
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving intent: {e}")
            raise


    @staticmethod
    def list_payments(customer_id=None, limit=10):
        """List payment intents."""
        try:
            if customer_id:
                intents = stripe.PaymentIntent.list(
                    customer=customer_id,
                    limit=limit
                )
            else:
                intents = stripe.PaymentIntent.list(limit=limit)
            
            return intents
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error listing payments: {e}")
            raise


    @staticmethod
    def handle_webhook(event):
        """Handle Stripe webhook events."""
        try:
            event_type = event['type']
            
            if event_type == 'payment_intent.succeeded':
                return handle_payment_succeeded(event['data']['object'])
            elif event_type == 'payment_intent.payment_failed':
                return handle_payment_failed(event['data']['object'])
            elif event_type == 'customer.subscription.deleted':
                return handle_subscription_cancelled(event['data']['object'])
            elif event_type == 'customer.subscription.updated':
                return handle_subscription_updated(event['data']['object'])
            elif event_type == 'charge.refunded':
                return handle_charge_refunded(event['data']['object'])
            
            logger.info(f"Unhandled Stripe event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {e}")
            raise


def handle_payment_succeeded(payment_intent):
    """Handle successful payment."""
    from funding.models import Donation
    from notifications.tasks import send_email_notification, send_donation_thank_you
    
    try:
        # Get or create donation record
        donation_id = payment_intent.get('metadata', {}).get('donation_id')
        
        if donation_id:
            donation = Donation.objects.get(id=donation_id)
            donation.status = 'completed'
            donation.stripe_payment_intent = payment_intent['id']
            donation.payment_date = timezone.now()
            donation.save()
            
            # Send thank you email
            send_donation_thank_you.delay(donation.id)
            
            logger.info(f"Payment succeeded for donation {donation_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment success: {e}")


def handle_payment_failed(payment_intent):
    """Handle failed payment."""
    from funding.models import Donation
    
    try:
        donation_id = payment_intent.get('metadata', {}).get('donation_id')
        
        if donation_id:
            donation = Donation.objects.get(id=donation_id)
            donation.status = 'failed'
            donation.save()
            
            logger.warning(f"Payment failed for donation {donation_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment failure: {e}")


def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation."""
    try:
        logger.info(f"Subscription cancelled: {subscription['id']}")
        # Add custom logic here
        
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")


def handle_subscription_updated(subscription):
    """Handle subscription update."""
    try:
        logger.info(f"Subscription updated: {subscription['id']}")
        # Add custom logic here
        
    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")


def handle_charge_refunded(charge):
    """Handle charge refund."""
    try:
        logger.info(f"Charge refunded: {charge['id']}")
        # Add custom logic here
        
    except Exception as e:
        logger.error(f"Error handling charge refund: {e}")
