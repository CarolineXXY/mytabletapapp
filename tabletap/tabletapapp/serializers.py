from rest_framework import serializers
from .models import MenuItem, Restaurant, Table, Order, Category, UserDetail

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ['restaurant']