
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from product.models import Region, Restaran
from django.http import JsonResponse
from rest_framework import status
from .models import CustomUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken



@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def api_register(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')
    password2 = data.get('password2')
    phone = data.get('phone')
    if password != password2:
        return JsonResponse({"message": "Passwords do not match.", 'success': False}, status=status.HTTP_400_BAD_REQUEST)
    if CustomUser.objects.filter(username=username).exists():
        return JsonResponse({"message": "Username already exists.", 'success': False}, status=status.HTTP_400_BAD_REQUEST)
    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        phone=phone
    )
    restaran = data.get('restaran')
    name = restaran.get('name')
    slug = restaran.get('slug')
    region = restaran.get('region')
    region = Region.objects.get_or_create(name=region)[0]
    desc = restaran.get('desc')
    lat = restaran.get('lat')
    lon = restaran.get('lon')
    restaran =  Restaran.objects.create(
        name=name,
        url=slug,
        region=region,
        description=desc,
        user=user,
        lat=lat,
        lon=lon
    )

    if user and restaran:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            "message": "Registration successful.",
            'success': True,
            'token': str(refresh.access_token),
            'refresh': str(refresh),
        })

    return JsonResponse({"message": "Registration failed.", 'success': False,}, status=status.HTTP_400_BAD_REQUEST)





@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return JsonResponse({
            "success": False,
            "message": "Login yoki parol noto'g'ri"
        }, status=401)

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    response = JsonResponse({
        "success": True,
        "message": "Login successful",
        "token": access_token,
        "refresh": str(refresh)
    })

    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=60 * 60 * 12,  # 12 soat
        path='/',
        samesite='Lax'
    )

    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        max_age=60 * 60 * 24 * 7,  # 7 kun
        path='/',
        samesite='Lax'
    )

    return response