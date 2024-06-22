from django.contrib import admin
from .models import CallbackRequests, Client, Order, ClientOrder

class AdminClientOrderInline(admin.TabularInline):
    model = ClientOrder
    extra = 0

    
@admin.register(CallbackRequests)
class AdminCallbackRequests(admin.ModelAdmin):

    model = CallbackRequests
    list_display = ('phone', 'request_time')
    extra = 0

@admin.register(Order)
class AdminOrder(admin.ModelAdmin):
    model = Order
    fields = ['__all__']
    extra = 0
    inlines = [AdminClientOrderInline]

@admin.register(Client)
class AdminClient(admin.ModelAdmin):

    model = Client
    list_display = ('name', 'phone', 'email')
    extra = 0
    inlines = [AdminClientOrderInline]