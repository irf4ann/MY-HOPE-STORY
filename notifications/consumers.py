"""
Django Channels consumers for real-time WebSocket communication.
Handles real-time notifications, live chat, and activity feeds.
"""

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    Users can receive live notifications without polling.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.user_group_name = f'notifications_{self.user.id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.id} connected to notifications")
    
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave notification group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user.id} disconnected from notifications")
    
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            
            elif command == 'mark_all_read':
                await self.mark_all_notifications_read()
            
            elif command == 'delete':
                notification_id = data.get('notification_id')
                await self.delete_notification(notification_id)
            
            elif command == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    
    async def notification_message(self, event):
        """Send notification to WebSocket."""
        notification = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': notification.get('id'),
            'title': notification.get('title'),
            'message': notification.get('message'),
            'action_url': notification.get('action_url'),
            'created_at': notification.get('created_at'),
            'icon': notification.get('icon'),
        }))
    
    
    async def activity_update(self, event):
        """Send activity update (like, comment, follow, etc)."""
        activity = event['activity']
        
        await self.send(text_data=json.dumps({
            'type': 'activity',
            'activity_type': activity.get('type'),  # 'like', 'comment', 'follow'
            'actor': activity.get('actor'),
            'object': activity.get('object'),
            'timestamp': activity.get('timestamp'),
        }))
    
    
    @sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        try:
            from notifications.models import Notification
            
            notification = Notification.objects.get(id=notification_id)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
            logger.info(f"Notification {notification_id} marked as read")
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
    
    
    @sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read for user."""
        try:
            from notifications.models import Notification
            
            Notification.objects.filter(
                recipient=self.user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            logger.info(f"All notifications marked as read for user {self.user.id}")
        except Exception as e:
            logger.error(f"Error marking all as read: {e}")
    
    
    @sync_to_async
    def delete_notification(self, notification_id):
        """Delete a notification."""
        try:
            from notifications.models import Notification
            
            Notification.objects.filter(id=notification_id).delete()
            logger.info(f"Notification {notification_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    Supports one-on-one and group chats.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id')
        self.chat_group_name = f'chat_{self.chat_id}'
        
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user is typing
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_join',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
            }
        )
        
        logger.info(f"User {self.user.id} connected to chat {self.chat_id}")
    
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Notify others that user left
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_leave',
                'user_id': self.user.id,
            }
        )
        
        # Leave chat group
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.id} disconnected from chat {self.chat_id}")
    
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'send_message':
                message_text = data.get('message', '').strip()
                
                if message_text:
                    # Save message to database
                    message = await self.save_message(message_text)
                    
                    # Broadcast message to chat group
                    await self.channel_layer.group_send(
                        self.chat_group_name,
                        {
                            'type': 'chat_message',
                            'id': message.get('id'),
                            'user_id': self.user.id,
                            'username': self.user.get_full_name(),
                            'message': message_text,
                            'timestamp': message.get('timestamp'),
                            'avatar': message.get('avatar_url'),
                        }
                    )
            
            elif command == 'typing':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': self.user.id,
                        'username': self.user.get_full_name(),
                    }
                )
            
            elif command == 'stop_typing':
                # Broadcast stop typing
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'user_stop_typing',
                        'user_id': self.user.id,
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in chat receive: {e}")
    
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp'],
            'avatar': event.get('avatar'),
        }))
    
    
    async def user_join(self, event):
        """Send user join notification."""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    
    async def user_leave(self, event):
        """Send user leave notification."""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
        }))
    
    
    async def user_typing(self, event):
        """Send typing indicator."""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    
    async def user_stop_typing(self, event):
        """Send stop typing indicator."""
        await self.send(text_data=json.dumps({
            'type': 'stop_typing',
            'user_id': event['user_id'],
        }))
    
    
    @sync_to_async
    def save_message(self, message_text):
        """Save message to database."""
        try:
            # TODO: Create ChatMessage model if not exists
            # message = ChatMessage.objects.create(
            #     chat_id=self.chat_id,
            #     user=self.user,
            #     content=message_text
            # )
            
            return {
                'id': '123',  # Would be message.id
                'timestamp': timezone.now().isoformat(),
                'avatar_url': self.user.avatar_url if hasattr(self.user, 'avatar_url') else None
            }
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return {}


# Helper functions to send notifications via WebSocket
async def send_notification_to_user(user_id, notification):
    """Send notification to a specific user via WebSocket."""
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f'notifications_{user_id}',
        {
            'type': 'notification_message',
            'notification': notification,
        }
    )


async def send_activity_update(user_id, activity):
    """Send activity update to a specific user via WebSocket."""
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f'notifications_{user_id}',
        {
            'type': 'activity_update',
            'activity': activity,
        }
    )
