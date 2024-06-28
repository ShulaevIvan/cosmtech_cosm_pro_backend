import datetime
import random
import os
import asyncio
import base64

from django.conf import settings
from django.utils import timezone
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, logout
from django.core.mail import send_mail
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import CallbackRequests, Client, Order, ClientOrder, ConsultRequest

class CallbackRequestView(APIView):
    permission_classes = [IsAuthenticated, ]
    def get(self, request):
        
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)
    
    def post(self, request):
        req_body = request.data
        not_format_date = datetime.datetime.now(tz=timezone.utc)
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
    
class RequestConsultView(APIView):

    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        req_body = request.data
        consult_data = {
            'name': req_body.get('name'),
            'phone': req_body.get('phone'),
            'email': req_body.get('email'),
            'city': req_body.get('city'),
            'comment': req_body.get('comment'),
        }

        if not consult_data['email'] and not consult_data['phone']:
            return Response({'status': 'not found', 'description': 'email or phone not valid'}, status=status.HTTP_200_OK)
        
        check_client = Client.objects.filter(Q(email=consult_data['email']) | Q(phone=consult_data['phone']))

        if not check_client.exists():
            Client.objects.create(
                name=consult_data['name'], 
                phone=consult_data['phone'], 
                email=consult_data['email'],
            ).save()

        ConsultRequest.objects.create(
            name=consult_data['name'], 
            phone=consult_data['phone'], 
            email=consult_data['email'],
            city=consult_data['city'],
            comment=consult_data['comment'],
            request_time = datetime.datetime.now(tz=timezone.utc)
        ).save()
        
        
        return Response({'status': 'ok', 'description': 'Ваш запрос принят!'}, status=status.HTTP_200_OK)

class RequestOrderView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    def post(self, request):

        req_body = request.data
        order_data = {
            "name": req_body.get('name'),
            "email": req_body.get('email'),
            "phone": req_body.get('phone'),
            "comment": req_body.get('comment'),
            "options": req_body.get('options')
        }
        
        if not order_data['email'] and not order_data['phone']:
            return Response({'status': 'not found', 'description': 'email or phone not valid'}, status=status.HTTP_200_OK)
        
        if order_data['email'] or order_data['phone']:
            if order_data['phone'] and order_data['email']:
                target_client = Client.objects.filter(email=order_data['email'], phone=order_data['phone'])
            elif order_data['email'] and not order_data['phone']:
                target_client = Client.objects.filter(email=order_data['email'])
            elif order_data['phone'] and not order_data['email']:
                target_client = Client.objects.filter(phone=order_data['phone'])
                
               
            if not target_client.exists():
                Client.objects.create(
                    name=order_data['name'], 
                    phone=order_data['phone'], 
                    email=order_data['email'],
                ).save()
                target_client = Client.objects.filter(name=order_data['name'], phone=order_data['phone'], email=order_data['email'])
            
            if not order_data['options']:
                order_data['options'] = 'none'

            order = generate_order_number('production', target_client[0].id)
            target_order, created = Order.objects.get_or_create(order_type=order['type'], order_date=order['date'])
            target_order.save()
            ClientOrder.objects.create(
                client_id=target_client.first(), 
                order_id=Order.objects.filter(id=target_order.id).first(),
                order_number = order['number'], 
                order_date = order['date'],
                oreder_description = order_data['comment'],
                order_option = order_data['options']
            ).save()
            
            not_format_date = datetime.datetime.now(tz=timezone.utc)
            time = get_time(not_format_date)

            # send_mail(
            #     'Новый запрос с сайта cosmtech.ru', 
            #     f"""Пришел запрос на (контрактное производство),
            #     Имя клиента: {order_data['name']};
            #     Телефон клиента: {order_data['phone']};
            #     Email клиента: {order_data['email']};
            #     Номер заказа: №{order['number']};
            #     Тип заказа: {order['type']};
            #     {time}""", 
            #     'django_mail@cosmtech.ru', ["pro@cosmtech.ru"]
            # )
            return Response({
                'message': 'ok', 'description': f"Спасибо! Запрос отправлен, Номер запроса: №{order['number']}"}, status=status.HTTP_201_CREATED)

        return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)
    
class ContactsRequestView(APIView):

    def post(self, request):
        req_body = request.data
        order_types = ['contract', 'lab', 'pack', 'cert']
        order_cooperations = ['trade', 'cooperation']
        contacts_data = {
            'name': req_body.get('name'),
            'email': req_body.get('email'),
            'phone': req_body.get('phone'),
            'orderType': req_body.get('orderType'),
            'city': req_body.get('city'),
            'comment': req_body.get('comment'),
            'file': req_body.get('file'),
        }

        if contacts_data['file'][0] and len(contacts_data['file']) > 0:
            files_list = contacts_data['file']
            for file in files_list:
                create_file(file, settings.ORDER_FILES)
        
        if contacts_data['orderType'] in order_types and contacts_data['orderType'] not in order_cooperations:
            target_client = find_existing_client(contacts_data['phone'], contacts_data['email'])
            if not target_client.exists():
                pass
            order = generate_order_number(contacts_data['orderType'], target_client[0].id)
            target_order, created = Order.objects.get_or_create(order_type=order['type'], order_date=order['date'])
            target_order.save()
            ClientOrder.objects.create(
                client_id=target_client.first(), 
                order_id=Order.objects.filter(id=target_order.id).first(),
                order_number = order['number'], 
                order_date = order['date'],
                oreder_description = contacts_data['comment'],
                order_option = contacts_data['orderType']
            ).save()
            
            not_format_date = datetime.datetime.now(tz=timezone.utc)
            time = get_time(not_format_date)

        return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)
    
def find_existing_client(phone='', email=''):
    if phone and email:
        target_client = Client.objects.filter(email=email, phone=phone)
    elif email and not phone:
        target_client = Client.objects.filter(email=email)
    elif phone and not email:
        target_client = Client.objects.filter(phone=phone)
    return target_client

def generate_order_number(order_type, client_id):
    order_modifer = []
    for i in range(4):
        order_modifer.append(chr(random.randint(ord('A'), ord('Z'))))

    order_modifer = ''.join(map(str, order_modifer))

    if not Order.objects.filter().exists():
        last_id = 1
        order_number = f'{client_id}-{order_modifer}-{last_id}'
        order_name = f'{order_number}'
    else:
        last_id = Order.objects.filter().latest('id')
        order_number = f'{client_id}-{order_modifer}-{last_id.id}'
        order_name = f'{order_number}'
    
    
    return {
        'name': order_name, 
        'type': order_type, 
        'number': order_number,
        'date': datetime.datetime.now(tz=timezone.utc)
    }

def create_file(file_obj, path):
    with open(f"{path}{file_obj['name']}", "wb") as file:
        file.write(base64.b64decode(file_obj['file']))

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

