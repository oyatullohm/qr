# restaran/serializers.py
from rest_framework import serializers
from .models import Restaran, Category, Menu, Region

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']



class MenuSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    category = CategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    image = serializers.ImageField(required=False)
    class Meta:
        model = Menu
        fields = [
            'id', 'name', 'price', 'price_discount',
            'is_discount', 'current_price',
            'description', 'image', 'is_active',
            'link_instagram', 'is_link_instagram',
            'order', 'category', 'category_id'
        ]

class CategoryWithMenusSerializer(serializers.ModelSerializer):
    """Kategoriya + ichidagi menyular — menu sahifasi uchun"""
    menus = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'menus']

    def get_menus(self, obj):
        # prefetch_related dan foydalanadi, yangi SQL yo'q
        active_menus = [m for m in obj.menus.all() if m.is_active]
        return MenuSerializer(active_menus, many=True, context=self.context).data

class RestoranProductSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    image = serializers.ImageField(read_only=True)
    class Meta:
        model = Restaran
        fields = [
            'id', 'url', 'name', 'description','service',
            'image', 'region', 'lat', 'lon', 'is_round',
        ]
        
        
# serializers.py
# from rest_framework import serializers
# from .models import Restaran, Menu, Category, Region
# from django.db.models import Count, Q



class CategorySerializer(serializers.ModelSerializer):
    menus = MenuSerializer(many=True, read_only=True)
    menu_count = serializers.SerializerMethodField()
    restaran_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'menus', 
            'menu_count',
            'restaran_count'
        ]
    
    def get_menu_count(self, obj):
        """Kategoriyadagi faol menyular soni"""
        return obj.menus.filter(is_active=True).count()
    
    def get_restaran_count(self, obj):
        """Kategoriyaga biriktirilgan restoranlar soni"""
        return obj.restaran.filter(is_active=True).count()


class RestoranSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    menu_count = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)
    has_menu = serializers.SerializerMethodField()
    top_dishes = serializers.SerializerMethodField()
    active_menus_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaran
        fields = [
            'id', 
            'name', 
            'slug', 
            'url', 
            'description',
            'image', 
            'is_active', 
            'service',
            'view_url',
            'lat', 
            'lon',
            'is_round',
            'region', 
            'categories',
            'menu_count',
            'has_menu',
            'top_dishes',
            'active_menus_count'
        ]
    
    def get_menu_count(self, obj):
        """Restorandagi barcha menyular soni"""
        return Menu.objects.filter(
            restaran=obj
        ).count()
    
    def get_active_menus_count(self, obj):
        """Restorandagi faol menyular soni"""
        return Menu.objects.filter(
            restaran=obj,
            is_active=True
        ).count()
    
    def get_has_menu(self, obj):
        """Restoranda menyu bormi"""
        return Menu.objects.filter(
            restaran=obj,
            is_active=True
        ).exists()
    
    def get_top_dishes(self, obj):
        """Eng ko'p ko'rilgan 3 ta taom"""
        menus = Menu.objects.filter(
            restaran=obj,
            is_active=True
        ).order_by('?')[:3]  # Random yoki view_url bo'yicha
        return MenuSerializer(menus, many=True).data


class RestoranListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun yengil serializer"""
    region = serializers.CharField(source='region.name', read_only=True)
    # category_names = serializers.SerializerMethodField()
    # menu_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaran
        fields = [
            'id',
            'name',
            'url',
            'region',
            'description',
            'image',
            'is_active',
            'is_round',
            'service',
            'view_url',
            'lat',
            'lon'
            # 'region_name',
            # 'category_names',
            # 'menu_count'
        ]
    
    # def get_category_names(self, obj):
    #     """Kategoriya nomlari ro'yxati"""
    #     return list(obj.categories.values_list('name', flat=True))
    
    # def get_menu_count(self, obj):
    #     """Menyular soni"""
    #     return Menu.objects.filter(restaran=obj).count()


class RestoranDetailSerializer(RestoranSerializer):
    """Batafsil ma'lumot uchun serializer"""
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta(RestoranSerializer.Meta):
        fields = RestoranSerializer.Meta.fields + ['user']
        read_only_fields = ['user']


class MenuSearchSerializer(serializers.ModelSerializer):
    """Qidiruv uchun menyu serializeri"""
    restaran_name = serializers.CharField(source='restaran.name', read_only=True)
    restaran_url = serializers.CharField(source='restaran.url', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'description',
            'price',
            'current_price',
            'image',
            'restaran_name',
            'restaran_url',
            'category_name'
        ]