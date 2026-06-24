# restaran/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Restaran

@receiver(post_save, sender=Restaran)
def clear_restoran_cache(sender, instance, **kwargs):
    cache.delete(f'restoran:slug:{instance.url}')
    cache.delete(f'restoran:id:{instance.id}')