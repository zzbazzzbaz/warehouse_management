from django.contrib import admin
from django.utils.html import format_html
from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'subtotal_display', 'created_at', 'updated_at']
    list_filter = ['created_at', 'user']
    search_fields = ['user__username', 'product__name']
    ordering = ['-updated_at']
    list_per_page = 20
    autocomplete_fields = ['user', 'product']
    
    def subtotal_display(self, obj):
        return format_html('<b>{}</b>', f'{obj.subtotal:.2f}')
    subtotal_display.short_description = '小计'
