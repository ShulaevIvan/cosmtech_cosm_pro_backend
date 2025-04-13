import re
from django.contrib import admin
from .models import CallbackRequests, Client, Order, ClientOrder, ConsultRequest, ClientOrderFile, \
    CoperationRequest, CoperationRequestFile, CityData, QuizOrder, QuizQuestionOrder, QuizTzOrder, Vacancy, \
    Supplier, SupplierType, ExcursionProductionRequest, SpecificationOrder, NewsItem, NewsBanner, NewsUrl, NewsVideo

class AdminClientOrderInline(admin.TabularInline):
    model = ClientOrder
    extra = 0
    fields = ['order_number', 'client_id', 'order_date', 'oreder_description',]
    ordering = ['order_date',]
    readonly_fields = ['order_date',]

class ClientOrderFileInline(admin.TabularInline):
    model = ClientOrderFile
    extra = 0
    fields = ['file_link',]
    readonly_fields = ['file_link',]

class CoperationRequestFileInline(admin.TabularInline):
    model = CoperationRequestFile
    extra = 0
    fields = ['file_link',]
    readonly_fields = ['file_link',]

class AdminNewsBannerInline(admin.TabularInline):
    model = NewsBanner
    extra = 0

class AdminNewsUrlInline(admin.TabularInline):
    model = NewsUrl
    extra = 0

class AdminNewsVideoInline(admin.TabularInline):
    model = NewsVideo
    extra = 0

@admin.register(CityData)
class CityDataAdmin(admin.ModelAdmin):
    model = CityData
    list_display = ['name', 'subject',]
    ordering=['name', 'subject',]
    search_fields = ['name', 'subject',]
    readonly_fields = ['name', 'subject', 'lat', 'lon', ]
    
@admin.register(QuizOrder)
class QuizOrderAdmin(admin.ModelAdmin):
    model = QuizOrder
    search_fields = ['order_number', 'client_name',]
    exclude = ['custom_tz_file', 'custom_package_file',]
    readonly_fields=[ 'package_file_link', 'tz_file_link',]

@admin.register(QuizQuestionOrder)
class QuizOrderQuestionAdmin(admin.ModelAdmin):
    model = QuizQuestionOrder
    search_fields = ['order_number', 'client_name',]
    list_display = ['order_number', 'order_date', 'client_name',]
    readonly_fields=['order_number', 'order_date',]

@admin.register(QuizTzOrder)
class QuizOrderTzAdmin(admin.ModelAdmin):
    model = QuizTzOrder
    search_fields = ['order_number', 'client_name',]
    exclude = ['tz_file',]
    list_display = ['order_number', 'order_date', 'client_name',]
    readonly_fields=['order_number', 'tz_file_link', 'order_date',]

@admin.register(CallbackRequests)
class AdminCallbackRequests(admin.ModelAdmin):
    model = CallbackRequests
    list_display = ['phone', 'request_time',]
    extra = 0

@admin.register(ConsultRequest)
class AdminConsultRequests(admin.ModelAdmin):

    model = ConsultRequest
    list_display = ['name', 'email', 'phone', 'comment', 'city', 'pref_communication', 'request_time',]
    extra = 0

@admin.register(Order)
class AdminOrder(admin.ModelAdmin):
    model = Order
    extra = 0
    list_display = ['order_type', 'order_date',]
    inlines = [AdminClientOrderInline]

@admin.register(Client)
class AdminClient(admin.ModelAdmin):

    model = Client
    list_display = ['name', 'phone', 'email',]
    extra = 0
    inlines = [AdminClientOrderInline]

@admin.register(ClientOrder)
class AdminClientOrders(admin.ModelAdmin):
    model = ClientOrder
    extra = 0
    fields = ['order_number', 'client_id', 'order_date', 'order_option', 'oreder_description', 'file_link',]
    list_display = ['order_number', 'client_id', 'order_date',]
    readonly_fields = ['order_date', 'file_link',]
    ordering = ['-order_date',]
    inlines=[ClientOrderFileInline]

@admin.register(CoperationRequest)
class AdminCoperationRequest(admin.ModelAdmin):
    model = CoperationRequest
    list_display = ['cooperation_type','name', 'email', 'phone',]
    extra = 0
    fields = ['cooperation_type','name', 'email', 'phone', 'request_description', 'file_link', 'request_time',]
    readonly_fields = ['request_time', 'file_link',]
    inlines=[CoperationRequestFileInline]

@admin.register(Vacancy)
class AdminVacancy(admin.ModelAdmin):
    model = Vacancy
    extra = 0
    
    def save_model(self, request, obj, form, change):
        check_pattern = r'^\s[2]|[•]'
        obj.requirements = ' '.join(re.sub(check_pattern, '', obj.requirements).split())
        obj.conditions = ' '.join(re.sub(check_pattern, '', obj.conditions).split())
        obj.dutys = ' '.join(re.sub(check_pattern, '', obj.dutys).split())
        obj.save()

@admin.register(Supplier)
class AdminSupplier(admin.ModelAdmin):
    model = Supplier

@admin.register(SupplierType)
class AdminSupplierType(admin.ModelAdmin):

    model = SupplierType
    fields=['name']

@admin.register(ExcursionProductionRequest)
class AdminExcursionProductionRequest(admin.ModelAdmin):

    model=ExcursionProductionRequest
    fields=['excursion_number', 'client_name', 'client_phone', 'excursion_date', 'excursion_time']

@admin.register(SpecificationOrder)
class AdminSpecificationOrder(admin.ModelAdmin):

    model = SpecificationOrder
    fields=['order_date', 'order_number', 'client_name',
        'client_email', 'client_phone', 'client_city',
        'product_type', 'product_category', 'product_name', 
        'product_params', 'product_segment', 'product_example_url', 
        'product_size','package_type', 'package_body', 
        'package_head', 'custom_package', 'services', 'delivery', 
        'quantity', 'tz_file_link', 'product_example_file_link'
    ]
    readonly_fields = [ 'order_date', 'order_number','tz_file_path', 'product_example_file', 'tz_file_link', 'product_example_file_link']

@admin.register(NewsItem)
class AdminNewsItem(admin.ModelAdmin):

    model = NewsItem
    inlines = [AdminNewsUrlInline, AdminNewsBannerInline, AdminNewsVideoInline]
