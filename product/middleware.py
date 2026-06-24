# product/middleware.py - to'liq yangilangan versiya
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import F

class JWTCookieMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def process_request(self, request):

        # Keraksiz joylarda ishlamasin
        if (
            request.path.startswith('/media/')
            or request.path.startswith('/static/')
            or request.path.startswith('/firebase-messaging-sw.js')
        ):
            return None

        # Faqat admin va api uchun ishlasin
        if not (
            request.path.startswith('/admin1/')
            or request.path.startswith('/api/')
        ):
            return None

        token = request.COOKIES.get('access_token')

        if not token:
            return None

        try:
            # Cache ishlatamiz
            cache_key = f"jwt_user:{hash(token)}"
            user = cache.get(cache_key)

            if user is None:
                validated_token = self.jwt_auth.get_validated_token(token)

                user_id = validated_token.get('user_id')

                if not user_id:
                    return None

                from main.models import CustomUser

                user = CustomUser.objects.only(
                    'id',
                    'username',
                    'is_active',
                    'is_staff',
                    'is_superuser'
                ).get(
                    id=user_id,
                    is_active=True
                )

                cache.set(cache_key, user, timeout=300)

            request.user = user
            request._cached_user = user

        except Exception:
            # Token expired yoki invalid
            pass

        return None

# product/middleware.py
from django.core.cache import cache
from django.db.models import F
from django.utils.deprecation import MiddlewareMixin
import threading
import time

class RestoranMiddleware(MiddlewareMixin):
    """Restoran ma'lumotlarini request ga qo'shadi (SESSION SIZ)"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
    
    def process_request(self, request):
        request.restoran = None
        path_parts = request.path.strip('/').split('/')
        
        # 🔥 1. URL dan slug orqali restoran olish
        if len(path_parts) >= 2 and path_parts[0] == 'r':
            slug = path_parts[1]
            request.restoran = self._get_restoran_by_slug(slug)
            
            if request.restoran:
                # 🔥 SESSION GA YOZMAYMIZ! Faqat request.restoran ishlatiladi
                # request.session['restoran_id'] = request.restoran.id  # ❌ O'CHIRILDI
                
                # Ko'rishlarni hisoblash
                self._add_view_count_optimized(request.restoran.id, request)
        
        # 🔥 2. Agar header da restoran_id bo'lsa (API uchun)
        elif 'HTTP_X_RESTORAN_ID' in request.META:
            restoran_id = request.META.get('HTTP_X_RESTORAN_ID')
            if restoran_id:
                request.restoran = self._get_restoran_by_id(restoran_id)
        
        # 🔥 3. Agar query parametrda restoran_id bo'lsa
        elif request.GET.get('restoran_id'):
            restoran_id = request.GET.get('restoran_id')
            request.restoran = self._get_restoran_by_id(restoran_id)
        
        return None
    
    def _get_restoran_by_slug(self, slug):
        """Slug bo'yicha restoran olish (cache bilan)"""
        cache_key = f'restoran:slug:{slug}'
        restoran = cache.get(cache_key)
        
        if restoran is None:
            try:
                from .models import Restaran
                restoran = Restaran.objects.select_related('region').only(
                    'id', 'name', 'url', 'description', 'image', 'service', 'is_active', 'region__name'
                ).get(url=slug, is_active=True)
                cache.set(cache_key, restoran, timeout=300)  # 5 minut
            except Restaran.DoesNotExist:
                return None
        return restoran
    
    def _get_restoran_by_id(self, restoran_id):
        """ID bo'yicha restoran olish (cache bilan)"""
        cache_key = f'restoran:id:{restoran_id}'
        restoran = cache.get(cache_key)
        
        if restoran is None:
            try:
                from .models import Restaran
                restoran = Restaran.objects.select_related('region').only(
                    'id', 'name', 'url', 'description', 'image', 'service', 'is_active', 'region__name'
                ).get(id=restoran_id, is_active=True)
                cache.set(cache_key, restoran, timeout=300)
            except Restaran.DoesNotExist:
                return None
        return restoran
    
    def _get_client_ip(self, request):
        """Client IP ni olish"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '')
    
    def _add_view_count_optimized(self, restoran_id, request):
        """Optimallashtirilgan ko'rishlar soni"""
        
        # Bir IP dan 5 minutda 1 marta
        client_ip = self._get_client_ip(request)
        cache_key_view = f'restoran_view_ip:{restoran_id}:{client_ip}'
        
        if cache.get(cache_key_view):
            return
        
        cache.set(cache_key_view, True, timeout=300)
        
        # Cache da yig'ish
        cache_key_count = f'restoran_view_count:{restoran_id}'
        try:
            current = cache.incr(cache_key_count)
        except:
            current = cache.get(cache_key_count, 0)
            cache.set(cache_key_count, current + 1, timeout=3600)
            current = current + 1
        
        # 100 ta ko'rish yoki 10 minutda bazaga yozish
        if current >= 100 or self._should_flush_to_db(restoran_id):
            self._async_flush_views(restoran_id)
    
    def _should_flush_to_db(self, restoran_id):
        """10 minutda 1 marta bazaga yozish"""
        cache_key = f'restoran_flush_time:{restoran_id}'
        last_flush = cache.get(cache_key)
        
        if not last_flush:
            cache.set(cache_key, time.time(), timeout=600)
            return False
        
        return (time.time() - last_flush) >= 600
    
    def _async_flush_views(self, restoran_id):
        """Async bazaga yozish"""
        cache_key_time = f'restoran_flush_time:{restoran_id}'
        cache.set(cache_key_time, time.time(), timeout=600)
        
        thread = threading.Thread(target=self._flush_views_to_db, args=(restoran_id,))
        thread.daemon = True
        thread.start()
    
    def _flush_views_to_db(self, restoran_id):
        """Cache dagi ko'rishlarni bazaga yozish"""
        cache_key_count = f'restoran_view_count:{restoran_id}'
        count = cache.get(cache_key_count, 0)
        
        if count > 0:
            try:
                from .models import Restaran
                Restaran.objects.filter(id=restoran_id).update(
                    view_url=F('view_url') + count
                )
                cache.delete(cache_key_count)
                print(f"[Views] Restoran {restoran_id}: +{count} view")
            except Exception as e:
                print(f"[Views] Xato: {e}")