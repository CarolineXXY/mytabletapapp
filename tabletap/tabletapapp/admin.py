from django.contrib import admin
from .models import UserDetail, Restaurant, Category, MenuItem, Table, Order, OrderItem

@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'role')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'table_count')
    search_fields = ('name', 'owner__user__username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'name', 'category', 'image', 'price')
    search_fields = ('name', 'category__name')

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'table_num', 'qr_code')
    search_fields = ('restaurant__name', 'table_num')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'table', 'cost', 'is_finished', 'order_time')
    search_fields = ('restaurant__name', 'table__table_num')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'price')
    search_fields = ('order__user__username', 'item__name')