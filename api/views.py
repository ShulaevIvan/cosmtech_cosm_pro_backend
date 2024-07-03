import datetime
import random
import base64
import re
import uuid
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.utils import timezone
from django.shortcuts import HttpResponse, render, get_object_or_404
from django.contrib.auth import authenticate, logout
from django.core.mail import send_mail
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import CallbackRequests, Client, Order, ClientOrder, ConsultRequest, ClientOrderFile, CoperationRequest, CoperationRequestFile

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
        file_path = ''
        contacts_data = {
            'name': req_body.get('name'),
            'email': req_body.get('email'),
            'phone': req_body.get('phone'),
            'orderType': req_body.get('orderType'),
            'call_option': req_body.get('callOption'),
            'city': req_body.get('city'),
            'comment': req_body.get('comment'),
            'file': req_body.get('file'),
        }
        client_data = {}
        client_files = []
        cooperation_files = []
        
        if contacts_data['orderType'] in order_types and contacts_data['orderType'] not in order_cooperations:
            target_client = find_existing_client(contacts_data['phone'], contacts_data['email'])
            if not target_client.exists():
                Client.objects.create(
                    name=contacts_data['name'], 
                    phone=contacts_data['phone'], 
                    email=contacts_data['email'],
                ).save()
                target_client = Client.objects.filter(name=contacts_data['name'], phone=contacts_data['phone'], email=contacts_data['email'])

            order = generate_order_number(contacts_data['orderType'], target_client[0].id)
            target_order, created = Order.objects.get_or_create(order_type=order['type'], order_date=order['date'])
            target_order.save()
            
            ClientOrder.objects.create(
                client_id=target_client.first(), 
                order_id=Order.objects.filter(id=target_order.id).first(),
                order_number = order['number'], 
                order_date = order['date'],
                oreder_description = contacts_data['comment'],
                order_option = contacts_data['orderType'],
                file = 'test'
            ).save()

            if contacts_data['file'] and len(contacts_data['file']) > 0:
                files_list = contacts_data['file']
                target_order = ClientOrder.objects.filter(order_number=order['number'])
               
                for file in files_list:
                    file_path = create_file(file, settings.ORDER_FILES)
                    ClientOrderFile.objects.create(client_order=ClientOrder.objects.get(id=target_order[0].id), file=file_path,).save()
                    client_files.append(file_path)
            
            client_data = {
                'client_name': contacts_data['name'],
                'client_phone': contacts_data['phone'],
                'client_email': contacts_data['email'],
                'call_option': get_request_name(contacts_data['call_option']),
                'client_comment': contacts_data['comment'],
                'order_number': order['number'],
                'order_type': order['type'],
                'order_type_name': get_request_name(contacts_data['orderType']),
            }
            client_data['files'] = client_files
            send_order_mail(client_data)

            return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)
        
        elif contacts_data['orderType'] in order_cooperations and contacts_data['orderType'] not in order_types:
            if contacts_data['phone'] or contacts_data['email']:
                cooperation_request, created = CoperationRequest.objects.get_or_create(
                    name = contacts_data['name'],
                    email = contacts_data['email'],
                    phone = contacts_data['phone'],
                    request_description = contacts_data['comment'],
                    cooperation_type = contacts_data['orderType'],
                )

                if contacts_data['file'] and len(contacts_data['file']) > 0:
                    files_list = contacts_data['file']
                    target_cooperation = CoperationRequest.objects.filter(id=cooperation_request.id)
                    for file in files_list:
                        file_path = create_file(file, settings.COOPERATION_FILES)
                        CoperationRequestFile.objects.create(
                            cooperation_request_id=CoperationRequest.objects.get(id=target_cooperation[0].id), 
                            file=file_path,
                        ).save()
                        cooperation_files.append(file_path)

                client_data = {
                    'client_name': contacts_data['name'],
                    'client_phone': contacts_data['phone'],
                    'client_email': contacts_data['email'],
                    'call_option': get_request_name(contacts_data['call_option']),
                    'order_type_name': get_request_name(contacts_data['orderType']),
                    'client_comment': contacts_data['comment'],
                }
                client_data['files'] = client_files
                send_order_mail(client_data)

                return Response(
                    {'message': 'ok', 'description': f"Спасибо! Запрос отправлен"}, 
                    status=status.HTTP_201_CREATED)
        
        return Response({'message': 'ok', 'description': f"err"}, status=status.HTTP_201_CREATED)
    
@permission_classes([IsAuthenticated,]) 
@api_view(['GET'])
def download_admin_file(request):
    params = request.query_params
    file_path = params.get('file_path')
    file_name = re.findall(r'[\w-]+\.\S+|\s+$', file_path)
    if len(file_name) > 0:
        file_name = file_name[0]
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read())
            response['Content-Disposition'] = 'attachment; filename=' + file_name
        
            return response
    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


def send_order_mail(client_data):
    if client_data['order_type_name'] is None:
        client_data['order_type_name'] = 'Контрактное производство'
    
    not_format_date = datetime.datetime.now(tz=timezone.utc)
    time = get_time(not_format_date)

    if client_data.get('order_number'):
        msg_mail = EmailMessage(
            f"Новый запрос {client_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({client_data['order_type_name']})</p>
                <p>Имя клиента: {client_data['client_name']}</p>
                <p>Телефон клиента: {client_data['client_phone']}
                <p>Email клиента: {client_data['client_email']}</p>
                <p>Предпочитаемый способ связи: {client_data['call_option']}</p>
                <p>Номер заказа: <b>№{client_data['order_number']}</b></p>
                <p>Тип заказа: {client_data['order_type_name']}</p>
                <p>Комментарий: {client_data['client_comment']}</p>
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', ["pro@cosmtech.ru"]
        )
    else:
        msg_mail = EmailMessage(
            f"Новый запрос {client_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({client_data['order_type_name']})</p>
                <p>Имя: {client_data['client_name']}</p>
                <p>Телефон: {client_data['client_phone']}
                <p>Email: {client_data['client_email']}</p>
                <p>Предпочитаемый способ связи: {client_data['call_option']}</p>
                <p>Тип запроса: {client_data['order_type_name']}</p>
                <p>Комментарий: {client_data['client_comment']}</p>
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', ["pro@cosmtech.ru"]
        )

    msg_mail.content_subtype = "html"  
    for file_path in client_data['files']:
        msg_mail.content_subtype = "html" 
        msg_mail.attach_file(f'{file_path}')
    msg_mail.send()

def send_mail_to_client():
    pass
    
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
    ext = re.findall(r'.\w+$', file_obj['name'])[0]
    full_name = f"{path}{uuid.uuid4()}{ext}"

    with open(full_name, "wb") as file:
        file.write(base64.b64decode(file_obj['file']))

    return full_name

def get_request_name(value):
    request_types = {
        'contract': 'Контрактное производство',
        'lab': 'Услуги лаборатории',
        'pack': 'Упаковка и сопровождение',
        'cert': 'Сертификаиця продукции',
        'trade': 'Торговое предложение',
        'cooperation': 'Сотрудничество',
        'msg': 'Мессанджеры',
        'phone': 'Телефон',
        'email': 'Email',

    }
    return request_types.get(value)

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

