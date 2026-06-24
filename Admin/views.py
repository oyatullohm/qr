# Admin/views.py

from django.shortcuts import redirect, render
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from product.models import Restaran
from django.core.cache import cache

def home(request):
    return render(request, 'restaran/home.html')


def menu(request, url):
    return render(request, 'restaran/menu.html', 
                  {'RESTORAN_SLUG': url}
                  )
def contract(request):
    url = request.GET.get('url', None)
    url = f"/r{url}"
    if url is not None:
        url = ''
    return render(  request, 
                    'restaran/shartnoma.html', 
                    {'url':url})

def auth(request):
    token = request.COOKIES.get("access_token")
    if token:
        try:
            JWTAuthentication().get_validated_token(token)
            return redirect("/admin1/")
        except Exception:
            pass

    response = render(request, "restaran/auth.html")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

def menuadmin(request):
    if not request.user.is_authenticated:
        return redirect('/auth/')
    return render(request, "restaran/menu-admin.html")

def qr_download(request):
    """QR kod yuklab olish sahifasi - view_url bilan"""
    
    # Tokenni tekshirish
    token = request.COOKIES.get('access_token')
    if not token:
        return redirect('/auth/')
    
    try:
        # Tokenni validatsiya qilish
        AccessToken(token)
    except TokenError:
        response = redirect('/auth/')
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
    
    # 🔥 Restoran ma'lumotlarini olish
    restoran = None
    view_count = 0
    
    try:
        # User ni tokendan olish
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        
        if user and user.is_authenticated:
            # User ga tegishli restoranni olish
            restoran = Restaran.objects.filter(user=user, is_active=True).first()
            
            if restoran:
                # 🔥 view_url ni olish
                view_count = restoran.view_url
                
                # 🔥 Cache dan real vaqt ko'rsatkichini olish (agar kerak bo'lsa)
                cache_count = cache.get(f'restoran_view_count:{restoran.id}', 0)
                if cache_count > 0:
                    view_count = restoran.view_url + cache_count
                
    except Exception as e:
        print(f"QR view error: {e}")
    
    context = {
        # 'restoran': restoran,
        'view_count': view_count,
        # 'restoran_name': restoran.name if restoran else 'Restoran',
        # 'restoran_url': restoran.url if restoran else '',
        # 'restoran_image': restoran.image.url if restoran and restoran.image else None,
        # 'service_percent': float(restoran.service) if restoran and restoran.service else 0,
    }

    return render(request, "restaran/qr-download.html", context)

# views.py
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from product.models import Restaran, Menu, Category
from product.serializers import (
    RestoranSerializer, 
    RestoranListSerializer,
    RestoranDetailSerializer,
    MenuSerializer, 
    MenuSearchSerializer,
    CategorySerializer
)

class RestoranListAPIView(generics.ListAPIView):
    """
    Restoranlar ro'yxati
    Endpoint: /api/restaurants/
    """
    serializer_class = RestoranListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'region__name']
    ordering_fields = ['name', 'service', 'view_url', 'is_active']
    ordering = ['-is_active', 'name']

    def get_queryset(self):
        qs = Restaran.objects.select_related('region').prefetch_related('categories')

        # Status filter
        status = self.request.query_params.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        # Halol filter - agar modelda bo'lsa

        region_id = self.request.query_params.get('region')
        if region_id:
            qs = qs.filter(region_id=region_id)

        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Statistik ma'lumotlar
        # total = queryset.count()
        # active = queryset.filter(is_active=True).count()
        # regions = queryset.values_list('region__name', flat=True).distinct().count()
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'results': serializer.data,
            # 'total': total,
            # 'active': active,
            # 'regions': regions
        })


class RestoranDetailAPIView(generics.RetrieveAPIView):
    """
    Restoran batafsil ma'lumot
    Endpoint: /api/restaurants/<slug:url>/
    """
    serializer_class = RestoranDetailSerializer
    lookup_field = 'url'
    lookup_url_kwarg = 'url'

    def get_queryset(self):
        return Restaran.objects.select_related('region').prefetch_related(
            'categories',
            'categories__menus'
        )


class MenuSearchAPIView(APIView):
    """
    Taomlar bo'yicha qidirish
    Endpoint: /api/menu/search/
    """
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({
                'results': [],
                'total': 0,
                'message': 'Qidiruv so\'zini kiriting'
            })

        # Menyulardan qidirish
        menus = Menu.objects.select_related(
            'restaran', 
            'category'
        ).filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).filter(
            restaran__is_active=True,
            is_active=True
        ).order_by('?')[:50]  # Random yoki view_url bo'yicha

        serializer = MenuSearchSerializer(menus, many=True)
        
        return Response({
            'results': serializer.data,
            'total': menus.count(),
            'query': query
        })


class RestoranSuggestAPIView(APIView):
    """
    Avtoto'ldirish (autocomplete)
    Endpoint: /api/restaurants/suggest/
    """
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if len(query) < 2:
            return Response({
                'results': [],
                'menus': [],
                'categories': []
            })

        # Restoranlar
        restaurants = Restaran.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).filter(is_active=True)[:10]

        # Menyular
        menus = Menu.objects.filter(
            Q(name__icontains=query)
        ).filter(
            restaran__is_active=True,
            is_active=True
        ).values_list('name', flat=True)[:10]

        # Kategoriyalar
        categories = Category.objects.filter(
            Q(name__icontains=query)
        ).filter(
            restaran__is_active=True
        ).values_list('name', flat=True)[:5]

        return Response({
            'restaurants': RestoranListSerializer(restaurants, many=True).data,
            'menus': list(menus),
            'categories': list(categories)
        })