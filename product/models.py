from django.db import models
from django.urls import reverse
from main.models import CustomUser
import os
class Region(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Hudud"
        verbose_name_plural = "Hududlar"

class Restaran(models.Model):
    url = models.SlugField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='restorans')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='restaran_images/', blank=True, null=True)
    # qr_image = models.ImageField(upload_to='qr_images/', blank=True, null=True)
    view_url = models.PositiveBigIntegerField(default=0)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    is_round = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    service = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('restaran_detail', kwargs={'url': self.url})
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['url']),
        ]
    def save(self, *args, **kwargs):
        try:
            old = Menu.objects.get(pk=self.pk)
        except Menu.DoesNotExist:
            old = None

        super().save(*args, **kwargs)

        if old and old.image and self.image:
            if old.image.name != self.image.name:
                old_path = old.image.path
                if os.path.isfile(old_path):
                    os.remove(old_path)

class Category(models.Model):
    name = models.CharField(max_length=255)
    restaran = models.ManyToManyField(Restaran, blank=True, related_name='categories')
    # image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        # 🔧 ManyToManyField ga indeks qo'yib bo'lmaydi, shuning uchun olib tashlandi
        # indexes = [models.Index(fields=['restaran'])]  # ❌ BUNI O'CHIRING

class Menu(models.Model):
    restaran = models.ForeignKey(
        Restaran,
        on_delete=models.CASCADE,
        related_name='menus'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='menus'
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # default qo'shildi
    is_discount = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    link_instagram = models.URLField(blank=True, null=True)
    is_link_instagram = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Menyu"
        verbose_name_plural = "Menyular"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['restaran', 'is_active']),
            models.Index(fields=['restaran', 'is_discount']),
            models.Index(fields=['restaran', 'order']),
            models.Index(fields=['category']),  # ForeignKey ga indeks qo'shish mumkin
        ]

    def __str__(self):
        return f"{self.name} — {self.restaran.name}"

    @property
    def current_price(self):
        """Chegirma bo'lsa discount narxni, bo'lmasa asosiy narxni qaytaradi"""
        return self.price_discount if self.is_discount else self.price
    
    def save(self, *args, **kwargs):
        try:
            old = Menu.objects.get(pk=self.pk)
        except Menu.DoesNotExist:
            old = None

        super().save(*args, **kwargs)

        if old and old.image and self.image:
            if old.image.name != self.image.name:
                old_path = old.image.path
                if os.path.isfile(old_path):
                    os.remove(old_path)