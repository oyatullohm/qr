
from django.contrib import admin
from django.urls import path, include
from . views import contract, menu,  home, auth, menuadmin, qr_download ,RestoranListAPIView
from rest_framework_simplejwt.views import TokenRefreshView 
from django.conf import settings
from django.conf.urls.static import static


from .views import (
    RestoranListAPIView, 
    MenuSearchAPIView,
    RestoranSuggestAPIView
)




from Admin import views
urlpatterns = [
    path('api/restaurants/', RestoranListAPIView.as_view(), name='restaurant-list'),
    path('api/restaurants/suggest/', RestoranSuggestAPIView.as_view(), name='restaurant-suggest'),
    path('api/menu/search/', MenuSearchAPIView.as_view(), name='menu-search'),

    path('', home, name='home'),
    path('r/<slug:url>/', menu, name='menu'), 
    path('auth/', auth, name='auth'),
    path('admin1/', menuadmin, name='menuadmin'),
    path('kattaadmin/', admin.site.urls),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/', include('product.urls')),
    path('api/auth/', include('main.urls')),
    path('qr/download/',qr_download, name='qr-download'),
    path('shartnoma/', contract, name='contract'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 
