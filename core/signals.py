from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

from .models import Profile, User



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)



@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()



from chat.models import Presence
@receiver(post_save, sender=Presence)
def touch_user_last_seen(sender, instance, **kwargs):
    User.objects.filter(id=instance.user_id).update(last_login=timezone.now())
    