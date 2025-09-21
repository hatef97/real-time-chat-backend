from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


from chat.models import Message
from chat.models.archive import ArchivedMessage



class Command(BaseCommand):
    help = "Archive messages older than N days (default 30)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **opts):
        cutoff = timezone.now() - timedelta(days=opts["days"])
        qs = Message.objects.filter(timestamp__lt=cutoff)[:5000]  # batch
        count = 0
        for m in qs:
            ArchivedMessage.objects.get_or_create(
                orig_id=m.id,
                defaults={
                    "chat_room": m.chat_room,
                    "sender": m.sender,
                    "content": m.content,
                    "timestamp": m.timestamp,
                },
            )
            m.delete()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Archived {count} messages"))
