"""
Local Notification Service - SNS Alternative
T054 - Local notification service (SNS alternative)

Provides local notification functionality as an alternative to AWS SNS.
Educational focus on understanding pub/sub messaging patterns while
maintaining local development capabilities.

AWS SNS comparison:
import boto3
sns = boto3.client('sns')
response = sns.publish(
    TopicArn='arn:aws:sns:region:account:topic',
    Message='notification message',
    Subject='subject'
)
"""

import json
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from queue import Queue, Empty
from pathlib import Path
from enum import Enum
import logging
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests

from settings import get_settings

settings = get_settings()


class NotificationType(Enum):
    """Notification types"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    SYSTEM = "system"


class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Subscriber:
    """
    Notification subscriber

    AWS SNS Subscription equivalent:
    {
        "SubscriptionArn": "arn:aws:sns:region:account:topic:subscription-id",
        "Protocol": "email",
        "Endpoint": "user@example.com",
        "TopicArn": "arn:aws:sns:region:account:topic"
    }
    """
    id: str
    protocol: NotificationType
    endpoint: str
    topic: str
    filter_policy: Optional[Dict[str, Any]] = None
    confirmed: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['protocol'] = self.protocol.value
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subscriber':
        """Create from dictionary"""
        data['protocol'] = NotificationType(data['protocol'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class Notification:
    """
    Notification message

    AWS SNS Message equivalent:
    {
        "MessageId": "uuid",
        "Message": "notification body",
        "Subject": "subject",
        "MessageAttributes": {"key": {"Type": "String", "Value": "value"}},
        "Timestamp": "2023-12-01T10:00:00.000Z"
    }
    """
    id: str
    topic: str
    message: str
    subject: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.attributes is None:
            self.attributes = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['sent_at'] = self.sent_at.isoformat() if self.sent_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create from dictionary"""
        data['status'] = NotificationStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['sent_at'] = datetime.fromisoformat(data['sent_at']) if data['sent_at'] else None
        return cls(**data)


class LocalNotificationService:
    """
    Local notification service mimicking AWS SNS functionality.

    Educational comparison:
    - Local topics: In-memory with disk persistence
    - AWS SNS: Managed pub/sub topics
    - Subscribers: Local handlers vs cloud endpoints
    - Delivery: Direct calls vs cloud infrastructure
    - Filtering: Custom logic vs SNS filter policies
    """

    def __init__(self, storage_root: str = None):
        """
        Initialize local notification service.

        Args:
            storage_root: Root directory for persistence
        """
        self.storage_root = Path(storage_root or settings.local_storage_root) / "notifications"
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Topics and subscribers
        self.topics: Set[str] = set()
        self.subscribers: Dict[str, List[Subscriber]] = {}  # topic -> subscribers
        self.subscribers_by_id: Dict[str, Subscriber] = {}

        # Notifications
        self.notifications: Dict[str, Notification] = {}
        self.notification_queue: Queue = Queue()

        # Worker thread
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False

        # Handlers for different protocols
        self.protocol_handlers: Dict[NotificationType, Callable] = {
            NotificationType.EMAIL: self._handle_email,
            NotificationType.SMS: self._handle_sms,
            NotificationType.WEBHOOK: self._handle_webhook,
            NotificationType.PUSH: self._handle_push,
            NotificationType.SYSTEM: self._handle_system
        }

        # Load persisted data
        self._load_data()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def create_topic(self, topic_name: str) -> str:
        """
        Create a notification topic.

        AWS SNS equivalent:
        response = sns.create_topic(Name='my-topic')
        topic_arn = response['TopicArn']

        Args:
            topic_name: Name of the topic

        Returns:
            Topic identifier (just the name for local implementation)
        """
        if topic_name in self.topics:
            return topic_name

        self.topics.add(topic_name)
        self.subscribers[topic_name] = []
        self._save_topics()

        self.logger.info(f"Created topic: {topic_name}")
        return topic_name

    def delete_topic(self, topic_name: str) -> bool:
        """
        Delete a notification topic.

        AWS SNS equivalent:
        sns.delete_topic(TopicArn=topic_arn)

        Args:
            topic_name: Name of the topic

        Returns:
            True if topic was deleted, False if not found
        """
        if topic_name not in self.topics:
            return False

        # Remove all subscribers
        for subscriber in self.subscribers.get(topic_name, []):
            del self.subscribers_by_id[subscriber.id]

        # Remove topic
        self.topics.remove(topic_name)
        del self.subscribers[topic_name]

        self._save_topics()
        self._save_subscribers()

        self.logger.info(f"Deleted topic: {topic_name}")
        return True

    def list_topics(self) -> List[str]:
        """
        List all topics.

        AWS SNS equivalent:
        response = sns.list_topics()
        topics = [t['TopicArn'] for t in response['Topics']]

        Returns:
            List of topic names
        """
        return list(self.topics)

    def subscribe(self, topic_name: str, protocol: NotificationType,
                 endpoint: str, filter_policy: Optional[Dict[str, Any]] = None) -> str:
        """
        Subscribe to a topic.

        AWS SNS equivalent:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint='user@example.com',
            Attributes={
                'FilterPolicy': json.dumps(filter_policy)
            }
        )

        Args:
            topic_name: Topic to subscribe to
            protocol: Notification protocol (email, sms, webhook, etc.)
            endpoint: Destination endpoint
            filter_policy: Optional message filtering rules

        Returns:
            Subscription ID
        """
        if topic_name not in self.topics:
            raise ValueError(f"Topic '{topic_name}' does not exist")

        subscriber = Subscriber(
            id=str(uuid.uuid4()),
            protocol=protocol,
            endpoint=endpoint,
            topic=topic_name,
            filter_policy=filter_policy
        )

        self.subscribers[topic_name].append(subscriber)
        self.subscribers_by_id[subscriber.id] = subscriber
        self._save_subscribers()

        self.logger.info(f"Subscribed {endpoint} to {topic_name} via {protocol.value}")
        return subscriber.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic.

        AWS SNS equivalent:
        sns.unsubscribe(SubscriptionArn=subscription_arn)

        Args:
            subscription_id: Subscription identifier

        Returns:
            True if unsubscribed, False if not found
        """
        subscriber = self.subscribers_by_id.get(subscription_id)
        if not subscriber:
            return False

        # Remove from topic list
        topic_subscribers = self.subscribers.get(subscriber.topic, [])
        self.subscribers[subscriber.topic] = [
            s for s in topic_subscribers if s.id != subscription_id
        ]

        # Remove from ID mapping
        del self.subscribers_by_id[subscription_id]
        self._save_subscribers()

        self.logger.info(f"Unsubscribed {subscriber.endpoint} from {subscriber.topic}")
        return True

    def list_subscriptions(self, topic_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List subscriptions, optionally filtered by topic.

        AWS SNS equivalent:
        response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)

        Args:
            topic_name: Optional topic filter

        Returns:
            List of subscription dictionaries
        """
        if topic_name:
            if topic_name not in self.topics:
                return []
            return [sub.to_dict() for sub in self.subscribers[topic_name]]

        return [sub.to_dict() for sub in self.subscribers_by_id.values()]

    def publish(self, topic_name: str, message: str, subject: Optional[str] = None,
               attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Publish a message to a topic.

        AWS SNS equivalent:
        response = sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject,
            MessageAttributes={
                'key': {'DataType': 'String', 'StringValue': 'value'}
            }
        )

        Args:
            topic_name: Topic to publish to
            message: Message content
            subject: Optional message subject
            attributes: Optional message attributes

        Returns:
            Notification ID
        """
        if topic_name not in self.topics:
            raise ValueError(f"Topic '{topic_name}' does not exist")

        notification = Notification(
            id=str(uuid.uuid4()),
            topic=topic_name,
            message=message,
            subject=subject,
            attributes=attributes or {}
        )

        self.notifications[notification.id] = notification
        self.notification_queue.put(notification)
        self._save_notification(notification)

        self.logger.info(f"Published notification {notification.id} to {topic_name}")
        return notification.id

    def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        Get notification delivery status.

        Args:
            notification_id: Notification identifier

        Returns:
            Notification status dictionary or None if not found
        """
        notification = self.notifications.get(notification_id)
        return notification.to_dict() if notification else None

    def start_worker(self) -> None:
        """Start the notification worker thread"""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name="NotificationWorker",
            daemon=True
        )
        self.worker_thread.start()
        self.logger.info("Started notification worker")

    def stop_worker(self) -> None:
        """Stop the notification worker thread"""
        if not self.running:
            return

        self.running = False
        self.notification_queue.put(None)  # Poison pill

        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
            self.worker_thread = None

        self.logger.info("Stopped notification worker")

    def get_topic_stats(self, topic_name: str) -> Dict[str, Any]:
        """
        Get topic statistics.

        Args:
            topic_name: Topic name

        Returns:
            Dictionary with topic stats
        """
        if topic_name not in self.topics:
            raise ValueError(f"Topic '{topic_name}' does not exist")

        subscribers = self.subscribers.get(topic_name, [])
        notifications = [n for n in self.notifications.values() if n.topic == topic_name]

        # Count by protocol
        protocol_counts = {}
        for subscriber in subscribers:
            protocol = subscriber.protocol.value
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1

        # Count by status
        status_counts = {}
        for notification in notifications:
            status = notification.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "topic": topic_name,
            "subscriber_count": len(subscribers),
            "notification_count": len(notifications),
            "protocol_breakdown": protocol_counts,
            "status_breakdown": status_counts
        }

    def _worker_loop(self) -> None:
        """Main worker loop for processing notifications"""
        self.logger.info("Notification worker started")

        while self.running:
            try:
                notification = self.notification_queue.get(timeout=1.0)
                if notification is None:  # Poison pill
                    break

                self._process_notification(notification)

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")

        self.logger.info("Notification worker stopped")

    def _process_notification(self, notification: Notification) -> None:
        """Process a single notification"""
        self.logger.info(f"Processing notification {notification.id}")

        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()

        try:
            # Get subscribers for the topic
            subscribers = self.subscribers.get(notification.topic, [])
            success_count = 0

            for subscriber in subscribers:
                if self._should_deliver(notification, subscriber):
                    try:
                        handler = self.protocol_handlers[subscriber.protocol]
                        handler(notification, subscriber)
                        success_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to deliver to {subscriber.endpoint}: {e}")

            if success_count > 0:
                notification.status = NotificationStatus.DELIVERED
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = "No successful deliveries"

        except Exception as e:
            self.logger.error(f"Notification {notification.id} failed: {e}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)

        self._save_notification(notification)

    def _should_deliver(self, notification: Notification, subscriber: Subscriber) -> bool:
        """Check if notification should be delivered to subscriber based on filter policy"""
        if not subscriber.filter_policy:
            return True

        # Simple filter policy implementation
        for key, expected_values in subscriber.filter_policy.items():
            actual_value = notification.attributes.get(key)
            if actual_value not in expected_values:
                return False

        return True

    def _handle_email(self, notification: Notification, subscriber: Subscriber) -> None:
        """Handle email notification delivery (mock implementation)"""
        self.logger.info(f"EMAIL to {subscriber.endpoint}: {notification.subject} - {notification.message[:50]}...")
        # In a real implementation, this would integrate with an email service

    def _handle_sms(self, notification: Notification, subscriber: Subscriber) -> None:
        """Handle SMS notification delivery (mock implementation)"""
        self.logger.info(f"SMS to {subscriber.endpoint}: {notification.message[:50]}...")
        # In a real implementation, this would integrate with an SMS service

    def _handle_webhook(self, notification: Notification, subscriber: Subscriber) -> None:
        """Handle webhook notification delivery"""
        try:
            payload = {
                "notification_id": notification.id,
                "topic": notification.topic,
                "message": notification.message,
                "subject": notification.subject,
                "attributes": notification.attributes,
                "timestamp": notification.created_at.isoformat()
            }

            response = requests.post(
                subscriber.endpoint,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            self.logger.info(f"WEBHOOK to {subscriber.endpoint}: {response.status_code}")

        except Exception as e:
            raise Exception(f"Webhook delivery failed: {e}")

    def _handle_push(self, notification: Notification, subscriber: Subscriber) -> None:
        """Handle push notification delivery (mock implementation)"""
        self.logger.info(f"PUSH to {subscriber.endpoint}: {notification.subject} - {notification.message[:50]}...")
        # In a real implementation, this would integrate with push notification services

    def _handle_system(self, notification: Notification, subscriber: Subscriber) -> None:
        """Handle system notification (log entry)"""
        self.logger.info(f"SYSTEM: {notification.topic} - {notification.message}")

    def _save_topics(self) -> None:
        """Persist topics to disk"""
        topics_file = self.storage_root / "topics.json"
        with open(topics_file, 'w') as f:
            json.dump(list(self.topics), f, indent=2)

    def _save_subscribers(self) -> None:
        """Persist subscribers to disk"""
        subscribers_file = self.storage_root / "subscribers.json"
        data = {
            topic: [sub.to_dict() for sub in subs]
            for topic, subs in self.subscribers.items()
        }
        with open(subscribers_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_notification(self, notification: Notification) -> None:
        """Persist notification to disk"""
        notification_file = self.storage_root / f"{notification.id}.json"
        with open(notification_file, 'w') as f:
            json.dump(notification.to_dict(), f, indent=2)

    def _load_data(self) -> None:
        """Load persisted data from disk"""
        # Load topics
        topics_file = self.storage_root / "topics.json"
        if topics_file.exists():
            try:
                with open(topics_file, 'r') as f:
                    self.topics = set(json.load(f))
            except (json.JSONDecodeError, ValueError):
                self.logger.warning("Failed to load topics")

        # Load subscribers
        subscribers_file = self.storage_root / "subscribers.json"
        if subscribers_file.exists():
            try:
                with open(subscribers_file, 'r') as f:
                    data = json.load(f)

                for topic, sub_data_list in data.items():
                    self.subscribers[topic] = []
                    for sub_data in sub_data_list:
                        subscriber = Subscriber.from_dict(sub_data)
                        self.subscribers[topic].append(subscriber)
                        self.subscribers_by_id[subscriber.id] = subscriber

            except (json.JSONDecodeError, ValueError):
                self.logger.warning("Failed to load subscribers")

        # Load notifications
        for notification_file in self.storage_root.glob("*.json"):
            if notification_file.name in ["topics.json", "subscribers.json"]:
                continue

            try:
                with open(notification_file, 'r') as f:
                    notification_data = json.load(f)

                notification = Notification.from_dict(notification_data)
                self.notifications[notification.id] = notification

            except (json.JSONDecodeError, ValueError):
                self.logger.warning(f"Failed to load notification from {notification_file}")


# Global notification service instance
_notification_service: Optional[LocalNotificationService] = None


def get_notification_service() -> LocalNotificationService:
    """Get the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = LocalNotificationService()
        _notification_service.start_worker()
    return _notification_service


# Educational Notes: Local Notifications vs AWS SNS
#
# 1. Topic Management:
#    - SNS: Managed topics with ARNs
#    - Local: String-based topic names
#    - Both support create/delete operations
#
# 2. Subscription Model:
#    - SNS: Protocol-based subscriptions (email, sms, http, etc.)
#    - Local: Custom protocol handlers
#    - Both support subscription confirmation
#
# 3. Message Filtering:
#    - SNS: JSON-based filter policies
#    - Local: Simple key-value matching
#    - Both enable targeted message delivery
#
# 4. Delivery Mechanisms:
#    - SNS: Cloud-managed delivery
#    - Local: Custom handlers for each protocol
#    - Both support webhooks and multiple protocols
#
# 5. Persistence:
#    - SNS: Built-in durability and retry
#    - Local: JSON file persistence
#    - Both ensure message delivery reliability
#
# 6. Monitoring:
#    - SNS: CloudWatch metrics and logs
#    - Local: Custom statistics and logging
#    - Both provide delivery status tracking