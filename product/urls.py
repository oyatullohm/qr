
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Admin uchun alohida router
admin_router = DefaultRouter()
admin_router.register('admin', views.AdminRestaranViewSet, basename='admin')
# Restoran uchun alohida router
restoran_router = DefaultRouter()
restoran_router.register(r'categories', views.CategoryViewSet, basename='category')
restoran_router.register(r'menus', views.MenuViewSet, basename='menu')
restoran_router.register(r'', views.RestoranViewSet, basename='restoran')

urlpatterns = [
    # path('menu/<int:pk>/', views.get_item, name='menu-item'),
    path('', include(admin_router.urls)),
    path('r/<slug:slug>/', include(restoran_router.urls)),
   
]
