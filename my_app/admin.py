from django.contrib import admin
from .models import Product
# Register your models here.

admin.site.site_header = "E-commerce Website"
admin.site.site_title = "Buying Website"
admin.site.index_title = "Manage E-commerce Website"
#showing the details of the product + search + actions
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','price','desc','seller_name')
    search_fields = ('name',)
    list_editable = ('price','desc','seller_name')
    def set_price_to_zero(self,request,queryset):
        return queryset.update(price=0)
    actions = ('set_price_to_zero',)

admin.site.register(Product,ProductAdmin)