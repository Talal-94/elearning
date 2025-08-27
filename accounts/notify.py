from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.urls import reverse
from .models import Notification

def create_and_push(recipient, verb: str, url: str = "", actor=None):
    notif = Notification.objects.create(
        recipient=recipient, actor=actor, verb=verb, url=url or ""
    )
    payload = {
        "id": notif.id,
        "verb": notif.verb,
        "url": notif.url,
        "created_at": notif.created_at.isoformat(),
        "unread_increment": 1,
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{recipient.id}",
        {"type": "notify", "payload": payload},
    )
    return notif
