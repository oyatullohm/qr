# restaran/views.py
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db.models import Count, Q , Prefetch
import os
from django.conf import settings
from .models import Restaran, Category, Menu
from rest_framework.exceptions import NotFound
from .serializers import (
    RestoranProductSerializer, CategorySerializer,
    CategoryWithMenusSerializer, MenuSerializer,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

class AdminRestaranViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_restoran(self, request):
        """Cache bilan optimallashtirilgan"""
        cache_key = f'restoran:user:{request.user.id}'
        restoran = cache.get(cache_key)
        
        if restoran is None:
            from django.db import connection
            restoran = get_object_or_404(
                Restaran.objects.only('id', 'name', 'url', 'description', 'image', 'service', 'is_active'),
                user=request.user,
                is_active=True
            )
            cache.set(cache_key, restoran, timeout=300)  # 5 daqiqa
        
        return restoran

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        restoran = self.get_restoran(request)
        
        # 🔥 CACHE dan statistikani olish (10 sekund)
        cache_key = f'dashboard:{restoran.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        # Bitta queryda menyular va kategoriyalar
        menus = list(Menu.objects.filter(restaran=restoran).select_related('category').only(
            'id', 'name', 'price', 'price_discount', 'is_discount', 'is_active',
            'description', 'image', 'link_instagram', 'is_link_instagram', 'order',
            'category__id', 'category__name'
        ))
        
        categories = list(Category.objects.filter(restaran=restoran).only('id', 'name'))
        
        # Python hisoblash (SQL yo'q)
        menu_count = len(menus)
        active_count = sum(1 for m in menus if m.is_active)
        discount_count = sum(1 for m in menus if m.is_discount)
        
        # Kategoriyalarni serialize qilish
        cat_map = {c.id: {'id': c.id, 'name': c.name} 
                for c in categories}
        
        # Menyularni serialize qilish
        menus_data = []
        for m in menus:
            menus_data.append({
                'id': m.id,
                'name': m.name,
                'price': str(m.price),
                'price_discount': str(m.price_discount),
                'is_discount': m.is_discount,
                'current_price': str(m.price_discount if m.is_discount else m.price),
                'description': m.description,
                'image': m.image.url if m.image else None,
                'is_active': m.is_active,
                'link_instagram': m.link_instagram,
                'is_link_instagram': m.is_link_instagram,
                'order': m.order,
                'category': {'id': m.category.id, 'name': m.category.name} if m.category else None
            })
        
        response_data = {
            'restoran': {
                'id': restoran.id,
                'name': restoran.name,
                'url': restoran.url,
                'description': restoran.description,
                'image': restoran.image.url if restoran.image else None,
                'service': str(restoran.service),
                'is_active': restoran.is_active,
            },
            'menu_count': menu_count,
            'category_count': len(categories),
            'active_count': active_count,
            'discount_count': discount_count,
            'categories': list(cat_map.values()),
            'menus': menus_data,
        }
        # print(response_data)
        # Cache ga saqlash (5 sekund - tez yangilanish uchun)
        cache.set(cache_key, response_data, timeout=5)
        
        return Response(response_data)    # PATCH /api/v1/admin/restoran/update/
    
    @action(detail=False, methods=['patch'])
    def update_restoran(self, request):
        restoran = self.get_restoran(request)
        
        if 'url' in request.data:
            new_url = request.data['url']
            # print(new_url)
        #     if Restaran.objects.exclude(id=restoran.id).filter(url=new_url).exists():
        #         return Response({'error': 'Bu URL band'}, status=status.HTTP_400_BAD_REQUEST)
            restoran.url = new_url

        
        if 'name' in request.data:
            restoran.name = request.data['name']
        
        if 'description' in request.data:
            restoran.description = request.data['description']
        
        if 'service' in request.data:
            restoran.service = request.data['service']


        if 'image' in request.FILES:
            if restoran.image:
                restoran.image.delete(save=False)
            restoran.image = request.FILES['image']

        restoran.save()
        
        serializer = RestoranProductSerializer(restoran, context={'request': request})
        return Response(serializer.data)

        # POST /api/v1/admin/menu/create/
    
    @action(detail=False, methods=['post'])
    def menu_create(self, request):
        restoran = self.get_restoran(request)

        data = request.data.copy()

        serializer = MenuSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(restaran=restoran)

        return Response(serializer.data)
  
    @action(detail=False, methods=['patch'], url_path='menu/(?P<menu_id>[0-9]+)/update')
    def menu_update(self, request, menu_id=None):
        restaran = self.get_restoran(request)

        menu = get_object_or_404(
            Menu,
            id=menu_id,
            restaran=restaran
        )

        serializer = MenuSerializer(
            menu,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
        

    @action(detail=False, methods=['delete'], url_path='menu/(?P<menu_id>[0-9]+)/delete')
    def menu_delete(self, request, menu_id=None):
        restaran = self.get_restoran(request)
        menu = get_object_or_404(Menu, id=menu_id, restaran=restaran)
        # menu image delete 
        menu.image.delete(save=False)
        menu.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # POST /api/v1/admin/category/create/
    @action(detail=False, methods=['post'])
    def category_create(self, request):
        restoran = self.get_restoran(request)
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cat = serializer.save()
        cat.restaran.add(restoran)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PATCH /api/v1/admin/category/<id>/update/
    @action(detail=False, methods=['patch'], url_path='category/(?P<cat_id>[0-9]+)/update')
    def category_update(self, request, cat_id=None):
        restaran = self.get_restoran(request)
        cat = get_object_or_404(Category, id=cat_id, restaran=restaran)
        serializer = CategorySerializer(cat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # DELETE /api/v1/admin/category/<id>/delete/
    @action(detail=False, methods=['delete'], url_path='category/(?P<cat_id>[0-9]+)/delete')
    def category_delete(self, request, cat_id=None):
        restaran = self.get_restoran(request)
        cat = get_object_or_404(Category, id=cat_id, restaran=restaran)
        cat.delete()  # agar boshqa restoranga tegishli bo‘lmasa
        if cat.restaran.count() == 0:
            cat.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    

class RestoranMixin:
    """Barcha ViewSet larda request.restoran ni tekshiradi (SESSION SIZ)"""
    permission_classes = [AllowAny]

    def get_restoran(self):
        """Request dan restoran olish (session ishlatilmaydi)"""
        
        # 🔥 1. request.restoran dan olish (middleware qo'ygan)
        if hasattr(self.request, 'restoran') and self.request.restoran:
            return self.request.restoran
        
        # 🔥 2. URL dan slug orqali olish
        slug = self.request.resolver_match.kwargs.get('slug')
        if slug:
            from product.models import Restaran
            try:
                restoran = Restaran.objects.get(url=slug, is_active=True)
                return restoran
            except Restaran.DoesNotExist:
                pass
        
        # 🔥 3. Header dan restoran_id olish
        restoran_id = self.request.META.get('HTTP_X_RESTORAN_ID')
        if restoran_id:
            from product.models import Restaran
            try:
                restoran = Restaran.objects.get(id=restoran_id, is_active=True)
                return restoran
            except Restaran.DoesNotExist:
                pass
        
        # 🔥 4. Query parametrdan restoran_id olish
        restoran_id = self.request.GET.get('restoran_id')
        if restoran_id:
            from product.models import Restaran
            try:
                restoran = Restaran.objects.get(id=restoran_id, is_active=True)
                return restoran
            except Restaran.DoesNotExist:
                pass
        
        raise NotFound("Restoran topilmadi")


class RestoranViewSet(RestoranMixin, viewsets.GenericViewSet):
    serializer_class = RestoranProductSerializer
    
    
    # GET /api/r/<slug>/
    def retrieve(self, request, url=None):
        restoran = self.get_restoran()
        serializer = self.get_serializer(restoran)
        return Response(serializer.data)

    # GET /api/r/<slug>/full/ — kategoriya + menyular birga
    @action(detail=False, methods=['get'], url_path='full')
    def full(self, request, slug=None):
        restoran = self.get_restoran()
        cache_key = f'restoran:full:{restoran.id}'
        data = cache.get(cache_key)

        if data is None:
            categories = Category.objects.filter(
                restaran=restoran
            ).order_by( 'name')

            data = {
                'restoran': RestoranProductSerializer(restoran, context={'request': request}).data,
                'categories': CategoryWithMenusSerializer(
                    categories, many=True, context={'request': request}
                ).data,
            }
            cache.set(cache_key, data, timeout=120)  # 2 daqiqa

        return Response(data)


class CategoryViewSet(RestoranMixin, viewsets.GenericViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(
            restaran=self.get_restoran()
        ).order_by('order', 'name')

    # GET /api/r/<slug>/categories/
    def list(self, request, url=None):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # GET /api/r/<slug>/categories/<pk>/
    def retrieve(self, request, url=None, pk=None):
        restaran = self.get_restoran()
        category = get_object_or_404(
            Category, pk=pk, restaran=restaran
        )
        serializer = self.get_serializer(category)
        return Response(serializer.data)

    # GET /api/r/<slug>/categories/<pk>/menus/
    @action(detail=True, methods=['get'])
    def menus(self, request, url=None, pk=None):
        restaran = self.get_restoran()
        category = get_object_or_404(Category, pk=pk, restaran=restaran)
        menus = Menu.objects.filter(
            restaran=restaran,
            category=category,
            is_active=True
        ).order_by('order', 'name')
        serializer = MenuSerializer(menus, many=True, context={'request': request})
        return Response(serializer.data)


class MenuViewSet(RestoranMixin, viewsets.GenericViewSet):
    serializer_class = MenuSerializer

    def get_queryset(self):
        restaran = self.get_restoran()

        qs = Menu.objects.filter(
            restaran=restaran,
            is_active=True
        ).select_related('category').order_by('name')

        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs

    # GET /api/r/<slug>/menus/
    def list(self, request, url=None):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # GET /api/r/<slug>/menus/<pk>/
    def retrieve(self, request, url=None, pk=None):
        restaran = self.get_restoran()
        menu = get_object_or_404(Menu, pk=pk, restaran=restaran, is_active=True)
        serializer = self.get_serializer(menu, context={'request': request})
        return Response(serializer.data)

