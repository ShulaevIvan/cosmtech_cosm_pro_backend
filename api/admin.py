from django.contrib import admin
from .models import CallbackRequests, Client, Order, ClientOrder, ConsultRequest


class AdminClientOrderInline(admin.TabularInline):
    model = ClientOrder
    extra = 0
    fields = ['order_number', 'client_id', 'order_date', 'oreder_description']
    ordering = ['order_date']
    readonly_fields = ['order_date']


@admin.register(CallbackRequests)
class AdminCallbackRequests(admin.ModelAdmin):

    model = CallbackRequests
    list_display = ('phone', 'request_time')
    extra = 0

@admin.register(ConsultRequest)
class AdminConsultRequests(admin.ModelAdmin):

    model = ConsultRequest
    list_display = ['name', 'email', 'phone', 'comment', 'city', 'pref_communication', 'request_time']
    extra = 0

@admin.register(Order)
class AdminOrder(admin.ModelAdmin):
    model = Order
    extra = 0
    list_display = ['order_type', 'order_date']
    inlines = [AdminClientOrderInline]

@admin.register(Client)
class AdminClient(admin.ModelAdmin):

    model = Client
    list_display = ['name', 'phone', 'email']
    extra = 0
    inlines = [AdminClientOrderInline]

@admin.register(ClientOrder)
class AdminClientOrders(admin.ModelAdmin):
    model = ClientOrder
    extra = 0
    fields = ['order_number', 'client_id', 'order_date', 'order_option', 'oreder_description']
    list_display = ['order_number', 'client_id', 'order_date']
    readonly_fields = ['order_date']
    ordering = ['-order_date']