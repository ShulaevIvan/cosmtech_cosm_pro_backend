import datetime
import uuid 
from django.utils import timezone
timezone.localtime(timezone.now())
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, logout
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from django.db.models import Q
from .models import CallbackRequests, Client, Order, ClientOrder

class CallbackRequestView(APIView):
    permission_classes = [IsAuthenticated, ]
    def get(self, request):
        
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)
    
    def post(self, request):
        req_body = request.data
        not_format_date = datetime.datetime.now()
        time = get_time(not_format_date)
        email_data = {
            'phone': req_body.get('phone'),
            'time': req_body.get('time'),
            'type': req_body.get('type'),
        }
        if email_data['phone']:
            CallbackRequests.objects.create(
                phone = email_data['phone'],
                name = '',
                request_time = not_format_date
            ).save()

            # send_mail(
            #     'Заказ обратного звонка', 
            #     f"Пришел запрос перезвонить клиенту по поводу консультации (контрактное производство)\n, Телефон клиента: {email_data['phone']}\n {time}", 
            #     'django_mail@cosmtech.ru', ["pro@cosmtech.ru"]
            # )

            return Response({
                'message': 'ok', 'description': 'Спасибо! Ваш запрос № 999 отправлен, вам перезвонят в течении 30 мин'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'err phone not valid'}, status=status.HTTP_200_OK)

class RequestOrderView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    def post(self, request):

        req_body = request.data
        order_data = {
            "name": req_body.get('name'),
            "email": req_body.get('email'),
            "phone": req_body.get('phone'),
            "comment": req_body.get('comment'),
        }
        
        if order_data['email'] or order_data['phone']:
            target_client = Client.objects.filter(Q(email=order_data['email']) | Q(phone=order_data['phone']))
            if not target_client.exists():
                target_client = Client.objects.create(
                    name=order_data['name'], 
                    phone=order_data['phone'], 
                    email=order_data['email'],
                ).save()
            target_order = Order.objects.create(order_type='production')
            target_order.save()
            client_order, created = ClientOrder.objects.get_or_create(
                client_id=target_client.first(), 
                order_id=Order.objects.filter(id=target_order.id).first(),
                order_number = uuid.uuid4(), 
            )

        return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)

def get_time(date):
    result_str = ''

    def add_zero_to_time(value):
        if value < 10:
            return f'0{value}'
        return value
    
    time_arr = [
        {"name": "hour", "value": date.hour},
        {"name": "minute", "value": date.minute},
        {"name": "second", "value": date.second},
        {"name": "day", "value": date.day},
        {"name": "month", "value": date.month},
        {"name": "year", "value": date.year},
    ]
    
    for time_obj in time_arr:
        time_obj['value'] = add_zero_to_time(time_obj['value'])
        if time_obj['name'] == 'hour' or time_obj['name'] == 'minute':
            time_obj['value'] = f"{time_obj['value']}:"
        elif time_obj['name'] == 'second':
            time_obj['value'] = f"{time_obj['value']} Дата: "
        elif time_obj['name'] == 'day' or time_obj['name'] == 'month':
            time_obj['value'] = f"{time_obj['value']}/"
        
        result_str = result_str + str(time_obj['value'])

    return f"Время: {result_str}"

