import datetime
import random
import base64
import re
import uuid
import os
import json
from django.views.generic.base import RedirectView
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from django.shortcuts import HttpResponse
from django.core.mail import send_mail
from django.db.models import Q
from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import CallbackRequests, Client, Order, ClientOrder, ConsultRequest, ClientOrderFile, \
    CoperationRequest, CoperationRequestFile, CityData, QuizOrder, QuizQuestionOrder, QuizTzOrder, \
    Vacancy, Supplier, SupplierType

def index(request):
    return render(request, 'index.html')

def default(request):
    path_list = ['/services', '/services/', '/contacts/', '/contacts', '/about', '/about/', '/job', '/job/', '/policy', '/policy/']
    path_ignore_list = ['/admin/', 'company_files/presentation/',]
    slash_pattern = re.compile(r'\s*\/$')
    find_slash = re.search(slash_pattern, request.path)
    target_url = list(filter(lambda url: url == request.path, path_list))
    print(request.path)

    if request.method == 'GET' and request.path in path_list and len(target_url) > 0:
        if find_slash:
            target_url = re.sub(slash_pattern, '', target_url[0])
            return redirect(f'{target_url}')
        return render(request, 'index.html')
    elif request.method == 'GET' and request.path not in path_ignore_list:
        # redirect('/page404')
        return render(request, '404.html', status=404)

    
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

            send_mail(
                'Заказ обратного звонка', 
                f"Пришел запрос перезвонить клиенту по поводу консультации (контрактное производство)\n, Телефон клиента: {email_data['phone']}\n {time}", 
                'django_mail@cosmtech.ru', ["pro@cosmtech.ru"]
            )

            return Response({
                'message': 'ok', 'description': 'Спасибо! Вам перезвонят в течении 30 мин'}, status=status.HTTP_201_CREATED)
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
            request_time = datetime.datetime.now()
        ).save()

        client_data = {
            'client_name': consult_data['name'],
            'client_phone': consult_data['phone'],
            'client_email': consult_data['email'],
            'client_city': consult_data['city'],
            'call_option': '',
            'order_type_name': 'Консультация',
            'client_comment': consult_data['comment'],
        }

        send_order_mail(client_data)
        send_mail_to_client(client_data)
        
        
        return Response({'status': 'ok', 'description': 'Спасибо, с вами свяжутся в ближайшее время!'}, status=status.HTTP_200_OK)

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
            order = generate_order_number(order_data['options'], target_client[0].id)
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
            
            client_data = {
                'client_name': order_data['name'],
                'client_phone': order_data['phone'],
                'client_email': order_data['email'],
                'order_number': order['number'],
                'call_option': '',
                'order_type_name': order_data['options'],
                'client_comment': order_data['comment'],
            }

            send_order_mail(client_data)
            send_mail_to_client(client_data)

            return Response({
                'message': 'ok', 'description': f"Спасибо! Запрос отправлен, Номер запроса: №{order['number']}"}, status=status.HTTP_201_CREATED)

        return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)
    
class ContactsRequestView(APIView):
    permission_classes = [IsAuthenticated, ]

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
                'client_city': contacts_data['city'],
                'call_option': get_request_name(contacts_data['call_option']),
                'client_comment': contacts_data['comment'],
                'order_number': order['number'],
                'order_type': order['type'],
                'order_type_name': get_request_name(contacts_data['orderType']),
            }
            client_data['files'] = client_files

            send_order_mail(client_data)
            send_mail_to_client(client_data)

            return Response(
                    {'message': 'ok', 'description': f"Спасибо! Запрос №{order['number']} зарегистрирован"}, 
                    status=status.HTTP_201_CREATED)
        
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
                    'client_city': contacts_data['city'],
                    'call_option': get_request_name(contacts_data['call_option']),
                    'order_type_name': get_request_name(contacts_data['orderType']),
                    'client_comment': contacts_data['comment'],
                }
                client_data['files'] = client_files

                send_order_mail(client_data)
                send_mail_to_client(client_data)

                return Response(
                    {'message': 'ok', 'description': f"Спасибо! Запрос отправлен"}, 
                    status=status.HTTP_201_CREATED)
        
        return Response({'message': 'ok', 'description': f"err"}, status=status.HTTP_201_CREATED)
    
class CityDataView(APIView):

    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        params = request.query_params
        city_param = params.get('city')
        check_dach = re.search('-', city_param)

        if not city_param:
            target_city = CityData.objects.all().values()
            return Response({'cities': target_city}, status=status.HTTP_200_OK)
        format_city_name = f'{city_param[0].upper()}{city_param[1:len(city_param)]}'
        
        if check_dach:
            name_part = city_param.split('-')
            format_city_name = f'{name_part[0][0].upper()}{name_part[0][1:len(name_part[0])]}-{name_part[1][0].upper()}{name_part[1][1:len(name_part[1])]}'

        city_name = fr'^{format_city_name}|^{format_city_name}(\w*|.*)(.|\w)(\w+)$'

        target_city = CityData.objects.filter(name__regex=city_name).values()

        return Response({'cities': target_city}, status=status.HTTP_200_OK)

class QuizOrderView(APIView):

    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        
        req_body = request.data
        client_name = req_body.get('name').get('value')
        client_phone = req_body.get('phone').get('value')
        client_email = req_body.get('email').get('value')
        send_data = req_body.get('sendData')
        order_data = dict()
        not_format_date = datetime.datetime.now()
        upload_folder = f'{os.getcwd()}/upload_files/quiz_files/'
        order_number = generate_quiz_order_number()
        order_time = get_time(not_format_date)
        order_folder_name = f'quiz_{order_number}'
        order_folder_path = f'{upload_folder}{order_folder_name}/'
        send_description = {
            'title': f'Спасибо за обращение {client_name}',
            'order': order_number,
            'description': 'Наш сотрудник пришлет рассчет/свяжется с вами в билижайшее время'
        }

        if not client_email or not client_phone:
            send_description = {
                'title': f'Спасибо за обращение {client_name}',
                'order': order_number,
                'description': 'Что-то пошло не так, пожалуйста продублируйте свой запрос на pro@cosmtech.ru '
            }
            return Response({'status': 'err', 'created': False, 'message': ''}, status=status.HTTP_200_OK)
        
        for key, value in send_data.items():
            re_pattern = r'\*?([A-Z])'
            start_index = list(re.finditer(re_pattern, key))[0].start()
            end_index = list(re.finditer(re_pattern, key))[0].end()
        
            replace_key = key[:start_index] + '_' + key[end_index -1:]
            order_data[replace_key.lower()] = value

        custom_delivery_city_to = ''
        custom_delivery_city_from = 'Санкт-Петербург'
        custom_delivery_range = 0
        custom_delivery_subject = ''
        custom_delivery_city_population = ''

        if order_data.get('custom_delivery') != 'empty':
            custom_delivery_city_to = order_data['custom_delivery']['to']
            custom_delivery_city_from = order_data['custom_delivery']['from']
            custom_delivery_range = order_data['custom_delivery']['range']
            custom_delivery_subject = order_data['custom_delivery']['subject']
            custom_delivery_city_population = order_data['custom_delivery']['population']

        custom_tz_file = order_data.get('custom_tz')
        custom_tz_file_url = ''
        custom_package_file = order_data.get('custom_package')
        custom_package_file_url = ''

        if (custom_tz_file != 'empty' or custom_package_file != 'empty') and not os.path.exists(f'{order_folder_path}'):
            os.mkdir(order_folder_path)

        if custom_tz_file != 'empty':
            custom_tz_file_url = create_file(custom_tz_file, order_folder_path)
            
        if custom_package_file != 'empty':
            custom_package_file_url = create_file(custom_package_file, order_folder_path)


        QuizOrder.objects.create(
            order_number=order_number,
            order_date=not_format_date,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            client_budget=order_data.get('client_budget'),
            order_deadline=order_data.get('order_deadline'),
            order_production_date=order_data.get('production_date'),
            order_service = order_data.get('order_service'),
            order_service_price=order_data.get('service_price'),
            order_product=order_data.get('product_name'),
            order_product_quantity=order_data.get('product_qnt'),
            order_product_package=order_data.get('order_package'),
            order_product_sum=int(order_data.get('calc_sum')),
            delivery_city_from=custom_delivery_city_from,
            delivery_city_to=custom_delivery_city_to,
            delivery_region=custom_delivery_subject,
            delivery_range=custom_delivery_range,
            delivery_weight=order_data.get('delivery_weight'),
            delivery_price_point=order_data.get('price_perpoint'),
            delivery_price= order_data.get('delivery_price'),
            custom_tz_file=custom_tz_file_url,
            custom_package_file=custom_package_file_url
        )
        email_data = {
            'order_type_name': 'Калькулятор производства',
            'order_number': order_number,
            'order_date':  get_time(not_format_date),
            'client_name': client_name,
            'client_email': client_email,
            'client_phone': client_phone,
            'client_budget': order_data.get('client_budget'),
            'order_deadline': order_data.get('order_deadline'),
            'order_production_date': order_data.get('production_date'),
            'order_service': order_data.get('order_service'),
            'order_service_price': order_data.get('service_price'),
            'order_product': order_data.get('product_name'),
            'order_product_quantity': order_data.get('product_qnt'),
            'order_product_package': order_data.get('order_package'),
            'order_product_sum': int(order_data.get('calc_sum')),
            'delivery_city_from': custom_delivery_city_from,
            'delivery_city_to': custom_delivery_city_to,
            'delivery_region': custom_delivery_subject,
            'delivery_range': custom_delivery_range,
            'delivery_weight': order_data.get('delivery_weight'),
            'delivery_price_point': order_data.get('price_perpoint'),
            'delivery_price': order_data.get('delivery_price'),
            'custom_tz_file': custom_tz_file_url,
            'custom_package_file': custom_package_file_url
        }

        send_quiz_result_to_email(email_data, 'quiz')
        send_quiz_to_client(email_data)

        return Response({'status': 'ok', 'created': True, 'message': send_description}, status=status.HTTP_201_CREATED)

class QuestionOrderView(APIView):

    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        req_body = request.data
        order_number = generate_quiz_order_number()
        not_format_date = datetime.datetime.now()
        client_name = req_body.get('name')
        client_phone = req_body.get('phone')
        client_email = req_body.get('email')
        client_question = req_body.get('comment')
        client_communication_type = req_body.get('communicationType')
        send_description = {
            'title': f'Спасибо за обращение {client_name}',
            'order': order_number,
            'description': 'Наш сотрудник свяжется с вами в течении 30 минут'
        }

        if not (client_phone or client_email):
            send_description = {
                'title': f'Спасибо за обращение {client_name}',
                'order': '',
                'description': 'Произошла ошибка, попробуйте позднее, либо напишите запрос на pro@cosmtech.ru'
            }
            return Response({'status': 'err', 'created': False, 'message': send_description}, status=status.HTTP_200_OK)
        
        QuizQuestionOrder.objects.create(
            order_number = order_number,
            order_date = not_format_date,
            client_name = client_name,
            client_phone = client_phone,
            client_email = client_email,
            communication_type = client_communication_type,
            client_question = client_question,
        )
        email_data = {
            'order_type_name': 'Задать вопрос технологу',
            'order_number': order_number,
            'order_date':  get_time(not_format_date),
            'client_name': client_name,
            'client_phone': client_phone,
            'client_email': client_email,
            'communication_type': client_communication_type,
            'client_question': client_question
        }
        send_quiz_result_to_email(email_data, 'question')
        send_quiz_to_client(email_data)

        return Response({'status': 'ok', 'created': True, 'message': send_description}, status=status.HTTP_201_CREATED)
    
class TzOrderView(APIView):

    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        req_body = request.data
        order_number = generate_quiz_order_number()
        not_format_date = datetime.datetime.now()
        order_time = get_time(not_format_date)
        upload_folder = f'{os.getcwd()}/upload_files/quiz_files/'
        order_folder_name = f'tz_{order_number}'
        order_folder_full_path = f'{upload_folder}{order_folder_name}/'
        client_name = req_body.get('name')
        client_phone = req_body.get('phone')
        client_email = req_body.get('email')
        client_tz_file = req_body.get('file')
        send_description = {
            'title': f'Спасибо за обращение {client_name}',
            'order': order_number,
            'description': 'Наш сотрудник свяжется с вами в течении 30 минут'
        }

        if not client_tz_file:
            send_description = {
                'title': f'Спасибо за обращение {client_name}',
                'order': order_number,
                'description': 'Произошла ошибка, попробуйте позднее, либо отправьте тз на pro@cosmtech.ru'
            }
            return Response({'status': 'err', 'created': False, 'message': send_description}, status=status.HTTP_200_OK)
        
        if not os.path.exists(f'{order_folder_full_path}'):
            os.mkdir(f'{order_folder_full_path}')
        tz_file_url = create_file(client_tz_file, f'{order_folder_full_path}')

        QuizTzOrder.objects.create(
            order_number = order_number,
            order_date = not_format_date,
            client_name = client_name,
            client_phone = client_phone,
            client_email = client_email,
            tz_file = tz_file_url,
        )
        email_data = {
            'order_type_name': 'Техническое Задание',
            'order_number': order_number,
            'order_date': order_time,
            'client_name': client_name,
            'client_phone': client_phone,
            'client_email': client_email,
            'tz_file': tz_file_url,
        }
        send_quiz_result_to_email(email_data, 'tz')
        send_quiz_to_client(email_data)

        return Response({'status': 'ok', 'created': True, 'message': send_description}, status=status.HTTP_201_CREATED)
    
class VacancyView(APIView):

    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        data = [
            { 
                'id': vacancy_obj['id'],
                'date':  get_time(vacancy_obj['open_date']),
                'name': vacancy_obj['name'],
                'departament': vacancy_obj['departament'],
                'salary': vacancy_obj['salary'],
                'phone': vacancy_obj['contact_phone'],
                'requirements': filter(lambda item: (item != '') , vacancy_obj['requirements'].split(';')),
                'conditions': filter(lambda item: (item != ''), vacancy_obj['conditions'].split(';')),
                'dutys': filter(lambda item: (item != ''), vacancy_obj['dutys'].split(';')),
            } 
            for vacancy_obj in Vacancy.objects.all().values()
        ]
        return Response({'vacancy': data}, status=status.HTTP_200_OK)
    
    def post(self, request):
        send_data = json.loads(request.body)
        vacancy_data = {
            'resume_name': send_data.get('name'),
            'resume_phone': send_data.get('phone'),
            'resume_file': send_data.get('file'),
            'vacancy_data': send_data.get('vacancy')
        }

        if not vacancy_data['resume_phone']:
            return Response({'status': 'err'})
        
        resume_folder_name = f"{vacancy_data['resume_name']}_{vacancy_data['vacancy_data']}_{vacancy_data['resume_phone']}"
        upload_folder = f'{os.getcwd()}/upload_files/resume_files/'
        resume_folder_full_path = f'{upload_folder}{resume_folder_name}/'
        file = ''

        if vacancy_data['resume_file']:
            if not os.path.exists(resume_folder_full_path):
                os.mkdir(resume_folder_full_path)
            vacancy_data['resume_file'] = create_file(vacancy_data['resume_file'], resume_folder_full_path)
        
        response_data = {
            'title': f"Спасибо {vacancy_data['resume_name']}, Ваш отклик очень важен для нас!",
            'description': 'Специалисты свяжутся с вами по телефону в ближайшее время'
        }

        send_vacancy_request(vacancy_data)

        return Response({'status': 'ok', 'data': response_data}, status=status.HTTP_201_CREATED)
    
class SupplierView(APIView):
    # permission_classes = [IsAuthenticated, ]
    
    def get(self, request):
        query_suppliers = Supplier.objects.all()
        supplier_data = [
            {
                "name": supplier_obj['name'],
                "city": supplier_obj['city'],
                "phone": supplier_obj['phone'],
                "phonelink": "".join(i for i in supplier_obj['phone'] if  i.isdecimal()),
                "url": supplier_obj['url'],
                "type": [type_obj for type_obj in SupplierType.objects.filter(id=supplier_obj['type_id']).values('name')][0]['name']

            } 
            for supplier_obj in query_suppliers.values()
        ]

        return Response({'status': 'ok', 'data': supplier_data}, status=status.HTTP_200_OK)

class SuppliersTypeView(APIView):
    # permission_classes = [IsAuthenticated, ]
    
    def get(self, request):
        query_suppliers_type = SupplierType.objects.all().values()

        return Response({'status': 'ok', 'data': query_suppliers_type}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_tz_template(request):
    download_param = request.query_params.get('download')
    tz_path = f'{os.getcwd()}/download/company_files/tz_template.docx'
    file_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if download_param:
        file_name = re.findall(r'[\w-]+\.\S+|\s+$', tz_path)[0]
        with open(f'{tz_path}', 'rb') as file:
            response = HttpResponse(file.read())
            response.headers = {
                "Content-Type": file_content_type,
                "Content-Disposition": f'attachment; filename="{file_name}"',
            }
            return response

    return FileResponse(open(f'{tz_path}', 'rb'), content_type=file_content_type, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def get_presentation(request):
    download_param = request.query_params.get('download')
    presentation_path = f'{os.getcwd()}/download/company_files/cosmtech-presentation.pdf'
    if download_param:
        file_name = re.findall(r'[\w-]+\.\S+|\s+$', presentation_path)[0]
        with open(f'{presentation_path}', 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/pdf')
            response.headers = {
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{file_name}"',
            }
            return response
   
    return FileResponse(open(f'{presentation_path}', 'rb'), content_type='application/pdf')
    
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
    
    not_format_date = datetime.datetime.now()
    time = get_time(not_format_date)

    if client_data.get('order_number'):
        msg_mail = EmailMessage(
            f"Новый запрос {client_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({client_data['order_type_name']})</p>
                <p>Имя клиента: {client_data['client_name']}</p>
                <p>Телефон клиента: {client_data['client_phone']}
                <p>Email клиента: {client_data['client_email']}</p>
                <p>Город клиента: {client_data.get('client_city')}</p>
                <p>Предпочитаемый способ связи: {client_data['call_option']}</p>
                <p>Номер заказа: <b>№{client_data['order_number']}</b></p>
                <p>Тип заказа: {client_data['order_type_name']}</p>
                <p>Комментарий: {client_data['client_comment']}</p>
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', [f"{settings.ORDER_MAIL}"]
        )
    elif not client_data.get('order_number'):
        msg_mail = EmailMessage(
            f"Новый запрос {client_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({client_data['order_type_name']})</p>
                <p>Имя: {client_data['client_name']}</p>
                <p>Телефон: {client_data['client_phone']}
                <p>Email: {client_data['client_email']}</p>
                <p>Город клиента: {client_data.get('client_city')}</p>
                <p>Предпочитаемый способ связи: {client_data['call_option']}</p>
                <p>Тип запроса: {client_data['order_type_name']}</p>
                <p>Комментарий: {client_data['client_comment']}</p>
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', [f"{settings.ORDER_MAIL}"]
        )

    if client_data.get('files'):
        msg_mail.content_subtype = "html"  
        for file_path in client_data['files']:
            msg_mail.attach_file(f'{file_path}')

    msg_mail.content_subtype = "html" 
    msg_mail.send()

def send_mail_to_client(order_data):
    not_format_date = datetime.datetime.now()
    time = get_time(not_format_date)
    if not order_data['client_email']:
        return
    if not order_data.get('order_number') and order_data.get('client_email'):
        msg_mail = EmailMessage(
            f"Ваш запрос  на {order_data['order_type_name']} отправлен", 
            f"""
                <p>Спасибо  {order_data['client_name']}! Ваш запрос зарегистрирован. С вами свяжутся в ближайшее время </p>
            """,
            'django_mail@cosmtech.ru', [f"{order_data['client_email']}"]
        )
        msg_mail.content_subtype = "html"  
        msg_mail.send()

        return
    
    elif order_data.get('order_number') and order_data.get('client_email'):
        msg_mail = EmailMessage(
            f"Ваш заказ на {order_data['order_type_name']} зарегистрирован", 
            f"""
                <p>Спасибо {order_data['client_name']} за проявленый интерес! Менеджеры свяжутся с вами в в ближайшее время </p>
                <p>Номер заказа: <b>{order_data['order_number']}</b></p>
                <p>Время запроса: <b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', [f"{order_data['client_email']}"]
        )
        msg_mail.content_subtype = "html"  
        msg_mail.send()

        return

def send_quiz_to_client(order_data):
    if not order_data['client_email']:
        return
    if order_data['order_type_name'] and order_data['client_name']:
        msg_mail = EmailMessage(
        f"Ваш запрос ({order_data['order_type_name']}) зарегистрирован", 
        f"""
            <p>Спасибо {order_data['client_name']} за проявленый интерес! Менеджеры свяжутся с вами в в ближайшее время </p>
            <p>Номер заказа: <b>{order_data['order_number']}</b></p>
            <p>Время запроса: <b>{order_data['order_date']}</b></p>
            <p>Вы всегда можете позвонить по телефону +7 (812) 363-06-14 для уточнения деталей.</p>
        """,
            'django_mail@cosmtech.ru', [f"{order_data['client_email']}"]
        )
        msg_mail.content_subtype = "html"  
        msg_mail.send()
        return

    
def send_quiz_result_to_email(quiz_data, order_type='quiz'):
    time = quiz_data.get('order_date')
    order_number = quiz_data.get('order_number')

    if order_type == 'question':
        msg_mail = EmailMessage(
            f"Новый запрос {quiz_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({quiz_data['order_type_name']})</p>
                <p>Имя: {quiz_data['client_name']}</p>
                <p>Телефон: {quiz_data['client_phone']}
                <p>Email: {quiz_data['client_email']}</p>
                <p>Предпочитаемый способ связи: {quiz_data['communication_type']}</p>
                <p><b>Вопрос</b>: {quiz_data['client_question']}</p>
                <p>Номер запроса ({order_number})</p>
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', [f"{settings.ORDER_MAIL}"]
        )
        msg_mail.content_subtype = "html"  
        msg_mail.send()

    if order_type == 'tz':
        msg_mail = EmailMessage(
            f"Новый запрос {quiz_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({quiz_data['order_type_name']})</p>
                <p>Имя: {quiz_data['client_name']}</p>
                <p>Телефон: {quiz_data['client_phone']}
                <p>Email: {quiz_data['client_email']}</p>
                <p>Номер запроса ({order_number})</p>
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', [f"{settings.ORDER_MAIL}"]
        )
        if quiz_data.get('tz_file'):
            msg_mail.content_subtype = "html" 
            print(quiz_data['tz_file'])
            msg_mail.attach_file(f"{quiz_data['tz_file']}")

        msg_mail.content_subtype = "html"  
        msg_mail.send()
    
    if order_type == 'quiz':
        msg_mail = EmailMessage(
            f"Новый запрос {quiz_data['order_type_name']} с сайта cosmtech.ru", 
            f"""
                <p>Пришел запрос на ({quiz_data['order_type_name']})</p>
                <p>Имя: {quiz_data['client_name']}</p>
                <p>Телефон: {quiz_data['client_phone']}
                <p>Email: {quiz_data['client_email']}</p>
                <p>Номер запроса ({order_number})</p>
                <p><b>{time}</b></p>
                <h4>Данные по запросу</h4>
                <table>
                    <tr><th>Продукт и услуги</th></tr>
                    <tr><td><b>Количество:</b> {quiz_data['order_product_quantity']} шт</td></tr>
                    <tr><td><b>Тип продукта:</b> {quiz_data['order_product']} </td></tr>
                    <tr><td><b>Упаковка:</b> {quiz_data['order_product_package']}мл</td></tr>
                    <tr><td><b>Бюджет:</b> {quiz_data['client_budget']}</td></tr>
                    <tr><td><b>Срок:</b> {quiz_data['order_deadline']}</td></tr>
                    <tr><td><b>Доп услуги:</b> {quiz_data['order_service']}</td></tr>
                    <tr><td><b>Бюджет:</b> {quiz_data['client_budget']} руб</td></tr>
                    <tr><td><b>Желаемые даты изготовления:</b> {quiz_data['order_production_date']}</td>
                    <tr><td><b>Приблизительный вес партии:</b> {quiz_data['delivery_weight']}</td></tr>
                </table>
                <h4>Доставка</h4>
                <p>Регион доставки {quiz_data['delivery_region']}</p>
                <p>Из {quiz_data['delivery_city_from']} в {quiz_data['delivery_city_to']}</p>
                <p>Расстоянеие в км от Салова 27 АБ по дорогам приблизительно:  {quiz_data['delivery_range']} км</p>
                <p>Средняя цена доставки за км {quiz_data['delivery_price_point']} руб</p>
                <h4>Стоимость</h4>
                <p>Озвучена приблизительная стоимость проекта:</p>
                <p>Стоимость доп услуг ({quiz_data['order_service']}): {quiz_data['order_service_price']} руб</p>
                <p>Приблизительная стоимость доставки {int(quiz_data['delivery_price_point']) * int(quiz_data['delivery_range'])} руб</p>
                <p>Полная сумма с учетом доп услуг: <b>{quiz_data['order_product_sum']} руб</b></p>
                <p>Прикреп. файлы 1 файл - ТЗ 2 файл - упаковка</p>
               
            """,
            'django_mail@cosmtech.ru', [f"{settings.ORDER_MAIL}"]
        )
        if quiz_data["custom_tz_file"]:
            msg_mail.attach_file(f'{quiz_data["custom_tz_file"]}')
        if quiz_data["custom_package_file"]:
            msg_mail.attach_file(f'{quiz_data["custom_package_file"]}')

        msg_mail.content_subtype = "html"  
        msg_mail.send()

def send_vacancy_request(send_data):
    not_format_date = datetime.datetime.now()
    time = get_time(not_format_date)
    msg_mail = EmailMessage(
            f"Новый отклик на вакансию {send_data['vacancy_data']} с сайта cosmtech.ru", 
            f"""
                <p>Вакансия({send_data['vacancy_data']})</p>
                <p>Имя({send_data['resume_name']})</p>
                <p>Телефон: {send_data['resume_phone']}
                <p><b>{time}</b></p>
            """,
            'django_mail@cosmtech.ru', [f"{settings.ORDER_MAIL}"]
    )
    msg_mail.content_subtype = "html"
    if send_data['resume_file']:
        msg_mail.attach_file(f'{send_data["resume_file"]}')
    msg_mail.send()
    
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
        'date': datetime.datetime.now()
    }

def generate_quiz_order_number():
    order_modifer = []
    for i in range(6):
        order_modifer.append(chr(random.randint(ord('A'), ord('Z'))))
    order_modifer.append('_qz_oer')
    order_modifer = f''.join(map(str, order_modifer))

    return order_modifer

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

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)
