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
            return format_html("<a href='%s'>download</a>" % (self.file.url,))
        else:
            return "No attachment"
    
class CoperationRequest(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, default='')
    email = models.CharField(max_length=255, null=True, blank=True, default='testmail@test.ru')
    phone = models.CharField(max_length=255, null=True, blank=True, default='0xxxxxxxxxx')
    request_description = models.TextField(null=True, blank=True)
    request_time = models.DateTimeField(auto_now_add=True)

    file = models.FileField(upload_to=f'upload_files/cooperation_files/', null=True, blank=True)

    def file_link(self):
        if self.file:
            return format_html("<a href='%s'>download</a>" % (self.file.url,))
        else:
            return "No attachment"