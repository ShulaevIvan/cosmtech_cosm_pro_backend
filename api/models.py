import re
import os
from django.db import models
from django.utils.html import format_html
# Create your models here.

class CallbackRequests(models.Model):
    phone = models.CharField(max_length=50, null=False, blank=False)
    name = models.CharField(max_length=100, null=True, blank=True, default='')
    request_time = models.DateTimeField()

    class Meta:
        verbose_name = 'callback_request'
        verbose_name_plural = 'callback_requests'

    def __str__(self):

        return self.phone
    
class ConsultRequest(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, default='')
    email = models.CharField(max_length=255, null=True, blank=True, default='testmail@test.ru')
    phone = models.CharField(max_length=255, null=True, blank=True, default='0xxxxxxxxxx')
    city = models.CharField(max_length=255, null=True, blank=True, default='')
    pref_communication = models.CharField(max_length=255, null=True, blank=True, default='')
    comment = models.TextField( null=True, blank=True, default='')
    request_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'consult_request'
        verbose_name_plural = 'consult_requests'

    def __str__(self):

        return self.phone
    
class Client(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, default='')
    email = models.CharField(max_length=255, null=True, blank=True, default='testmail@test.ru')
    phone = models.CharField(max_length=255, null=True, blank=True, default='0xxxxxxxxxx')
    orders = models.ManyToManyField('Order', through='ClientOrder')

    class Meta:
        verbose_name = 'client_info'
        verbose_name_plural = 'clients_info'

    def __str__(self):
        
        return self.name

class Order(models.Model):
    order_type = models.CharField(null=True, blank=True, default='production')
    order_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'order'
        verbose_name_plural = 'orders'


    def __str__(self):

        return self.order_type
    
class ClientOrder(models.Model):
    order_number = models.CharField(max_length=255)
    order_date = models.DateTimeField(auto_now_add=True)
    order_option = models.CharField(max_length=255, null=True, blank=True, default='none')
    oreder_description = models.TextField(null=True, blank=True, default='')
    file = models.FileField(upload_to=f'upload_files/order_files/', null=True, blank=True)

    client_id = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_order')
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_client')

    class Meta:
        
        verbose_name = 'client_order'
        verbose_name_plural = 'clients_orders'

    def __str__(self):

        return self.order_number
    
    def file_link(self):
        if self.file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.file.url}' target=blank>download file</a>")
        else:
            return "No attachment"
        
class ClientOrderFile(models.Model):
    file = models.FileField(upload_to=f'upload_files/order_files/', null=True, blank=True, max_length=255)
    file_name = models.TextField(null=True, blank=True, default='file', max_length=255)
    file_type = models.CharField(null=True, blank=True, default='')
    client_order = models.ForeignKey(ClientOrder, on_delete=models.CASCADE, related_name='client_files')

    def file_link(self):
        if self.file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.file.url}' target=blank>download file</a>")
        else:
            return "No attachment"
        
    def __str__(self):

        return f'{self.client_order.client_id.name} file'
    
    
class CoperationRequest(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, default='')
    email = models.CharField(max_length=255, null=True, blank=True, default='testmail@test.ru')
    phone = models.CharField(max_length=255, null=True, blank=True, default='0xxxxxxxxxx')
    request_description = models.TextField(null=True, blank=True)
    cooperation_type = models.CharField(max_length=255, null=True, blank=True)
    request_time = models.DateTimeField(auto_now_add=True)

    file = models.FileField(upload_to=f'upload_files/cooperation_files/', null=True, blank=True)

    def __str__(self):

        return self.cooperation_type

    def file_link(self):
        if self.file:
            return format_html("<a href='%s'>download</a>" % (self.file.url,))
        else:
            return "No attachment"
        
class CoperationRequestFile(models.Model):
    file = models.FileField(upload_to=f'upload_files/cooperation_files/', null=True, blank=True, max_length=255)
    file_name = models.TextField(null=True, blank=True, default='file', max_length=255)
    file_type = models.CharField(null=True, blank=True, default='')
    cooperation_request_id = models.ForeignKey(CoperationRequest, on_delete=models.CASCADE, related_name='cooperation_request_file')

    def file_link(self):
        if self.file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.file.url}' target=blank>download file</a>")
        else:
            return "No attachment"
        
    def __str__(self):

        return f'{self.file_name}'

class CityData(models.Model):
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    population = models.IntegerField()
    range = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()

    def __str__(self):

        return f'{self.name}'
    
class QuizOrder(models.Model):
    order_number = models.CharField(max_length=255)
    order_date = models.DateTimeField(auto_now_add=True)
    client_name = models.CharField(max_length=255, default='')
    client_email = models.CharField(max_length=255, default='testmail@test.ru')
    client_phone = models.CharField(max_length=255, default='0xxxxxxxxxx')
    client_budget = models.CharField(max_length=255, null=True, blank=True)
    order_deadline = models.TextField(null=True, blank=True)
    order_production_date = models.CharField(max_length=255, null=True, blank=True)
    order_service = models.CharField(max_length=255, null=True, blank=True)
    order_service_price = models.IntegerField(null=True, blank=True)
    order_product = models.CharField(max_length=255)
    order_product_quantity = models.IntegerField()
    order_product_package = models.TextField(null=True, blank=True)
    order_product_sum = models.IntegerField(null=True, blank=True)
    delivery_city_from = models.CharField(null=True, blank=True)
    delivery_city_to = models.CharField(null=True, blank=True)
    delivery_region = models.CharField(max_length=255, blank=True, null=True)
    delivery_range = models.IntegerField(null=True, blank=True)
    delivery_weight = models.CharField(null=True, blank=True)
    delivery_price_point = models.IntegerField(null=True, blank=True)
    delivery_price = models.IntegerField(null=True, blank=True)
    custom_tz_file =  models.FileField(upload_to=f'upload_files/quiz_files/{order_number}/', null=True, blank=True, max_length=255)
    custom_package_file = models.FileField(upload_to=f'upload_files/quiz_files/{order_number}/', null=True, blank=True, max_length=255)

    def tz_file_link(self):
        if self.custom_tz_file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.custom_tz_file.url}' target=blank>download file</a>")
        else:
            return "No attachment"
        
    def package_file_link(self):
        if self.custom_package_file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.custom_package_file.url}' target=blank>download file</a>")
        else:
            return "No attachment"
        

    def __str__(self):

        return f'{self.order_number}'
    
class QuizQuestionOrder(models.Model):
    order_number = models.CharField(max_length=255)
    order_date = models.DateTimeField(auto_now_add=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    client_phone = models.CharField(max_length=255, null=True, blank=True, default='0xxxxxxxxxx')
    client_email = models.CharField(max_length=255, null=True, blank=True, default='testmail@test.ru')
    communication_type = models.CharField(null=True, blank=True)
    client_question = models.TextField(null=True, blank=True)

    def __str__(self):

        return f'{self.order_number}'

class QuizTzOrder(models.Model):
    order_number = models.CharField(max_length=255)
    order_date = models.DateTimeField(auto_now_add=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    client_phone = models.CharField(max_length=255, null=True, blank=True, default='0xxxxxxxxxx')
    client_email = models.CharField(max_length=255, null=True, blank=True, default='testmail@test.ru')
    tz_file = models.FileField(upload_to=f'upload_files/quiz_files/{order_number}/', max_length=255)

    def tz_file_link(self):
        if self.tz_file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.tz_file.url}' target=blank>download file</a>")
        else:
            return "No attachment"

    def __str__(self):

        return f'{self.order_number}'
    
class Vacancy(models.Model):
    name = models.CharField(max_length=255)
    open_date = models.DateTimeField(auto_now_add=True)
    departament = models.CharField(max_length=255)
    salary = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=255, null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    conditions = models.TextField(null=True, blank=True)
    dutys = models.TextField(null=True, blank=True)

    def __str__(self):

        return f'{self.name} / {self.salary}'
    
class SupplierType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        
        return f'{self.name}'
    
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    url = models.URLField(null=True, blank=True)
    type = models.ForeignKey(SupplierType, on_delete=models.CASCADE, related_name='supplier_type')

    def __str__(self):

        return f'{self.name} | {self.type}'

class ExcursionProductionRequest(models.Model):
    excursion_number = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    client_phone = models.CharField(max_length=20)
    excursion_date = models.DateTimeField()
    excursion_time = models.TimeField()

    def __str__(self):
        return f"{self.client_name} {self.excursion_time} {str(self.excursion_date).replace('00:00:00', '')}"
    
class SpecificationOrder(models.Model):
    order_date = models.DateTimeField()
    order_number = models.CharField(max_length=255)
    client_name = models.CharField(max_length=100)
    client_email = models.CharField(max_length=100, blank=True, null=True)
    client_phone = models.CharField(max_length=100, blank=True, null=True)
    client_city = models.CharField(max_length=255, blank=True, null=True)
    product_type = models.CharField(max_length=255)
    product_category = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    product_params = models.TextField(null=True, blank=True)
    product_segment = models.CharField(max_length=255)
    product_example_url = models.URLField(null=True, blank=True)
    product_size = models.CharField(max_length=100)
    package_type = models.CharField(max_length=100)
    package_body = models.CharField(max_length=100, null=True, blank=True)
    package_head = models.CharField(max_length=100, null=True, blank=True)
    custom_package = models.CharField(max_length=255, null=True, blank=True)
    services = models.TextField(null=True, blank=True)
    delivery = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField()
    tz_file_path = models.FilePathField(max_length=255, null=True, blank=True)
    product_example_file = models.FilePathField(max_length=255, null=True, blank=True)

    def __str__(self):
        format_date = re.sub(r'\.\d+$', '', str(self.order_date))
        return f"ТЗ от {self.client_name} №{self.order_number} {format_date}"
    
    def tz_file_link(self):
        if self.tz_file_path:
            return format_html(f"<a href='/api/admin_download/?file_path={self.tz_file_path}' target=blank>download file</a>")
        else:
            return "No attachment"
        
    def product_example_file_link(self):
        if self.product_example_file:
            return format_html(f"<a href='/api/admin_download/?file_path={self.product_example_file}' target=blank>download file</a>")
        else:
            return "No attachment"

class NewsItem(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    min_img = models.ImageField(
        null=True, 
        blank=True, 
        upload_to='upload_files/news_files/', 
        default=f'upload_files/news_fiels/news_default_img.png'
    )
    min_img_alt = models.CharField(null=True, blank=True, default='min_alt')
    short_description = models.TextField()

    text_content = models.TextField()

    def __str__(self):
        return f'{self.title} от {self.date}'

class NewsUrl(models.Model):
    news_url = models.URLField()
    url_text = models.CharField(max_length=255, null=True, blank=True, default='url text')
    news_id = models.ForeignKey(NewsItem, on_delete=models.CASCADE, related_name='news_url')

class NewsVideo(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to=f'upload_files/news_files/videos')
    mode = models.CharField(null=True, blank=True, default='video')
    text = models.TextField(null=True, blank=True)
    news_id = models.ForeignKey(NewsItem, on_delete=models.CASCADE, related_name='news_video')

class NewsBanner(models.Model):
    news_image = models.FileField(upload_to=f'upload_files/news_files/banners')
    alt_text = models.CharField(max_length=255, null=True, blank=True, default='alt image')
    news_id = models.ForeignKey(NewsItem, on_delete=models.CASCADE, related_name='news_image')