import re
import os
import json
from pprint import pprint
from datetime import datetime
import datetime as dt
from django.views.generic.base import RedirectView
from django.shortcuts import render, redirect
from django.conf import settings
from django.shortcuts import HttpResponse
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import sync_to_async
from adrf.views import APIView
from .utils import validate_email, create_specification_file, create_file, get_request_name, \
    generate_order_number, get_time, find_existing_data_by_contact, get_all_data_from_model, \
    read_json_file_by_parh

from.utils import write_access_view_err_log, select_email_template_by_order, select_client_email_template_by_order, \
    send_order_to_main_email, send_email_to_client, file_to_base64, get_paragraphs_from_text, get_currency_daily_course

from .models import CallbackRequests, Client, Order, ClientOrder, ConsultRequest, ClientOrderFile, \
    CoperationRequest, CoperationRequestFile, CityData, QuizOrder, QuizQuestionOrder, QuizTzOrder, \
    Vacancy, Supplier, SupplierType, ExcursionProductionRequest, SpecificationOrder, NewsItem, NewsBanner, NewsVideo, NewsUrl

def index(request):
    return render(request, 'index.html')

def default(request):
    path_list = [
        '/services', '/services/', '/contacts/', 
        '/contacts', '/about', '/about/', 
        '/job', '/job/', '/policy', 
        '/policy/', '/forclients/', '/forclients',
        'robots.txt', 'sitemap.xml'
    ]
    path_ignore_list = ['/admin/', 'company_files/presentation/', 'robots.txt/', '/robots.txt', '/sitemap.xml', 'sitemap.xml/']
    slash_pattern = re.compile(r'\s*\/$')
    find_slash = re.search(slash_pattern, request.path)
    target_url = list(filter(lambda url: url == request.path, path_list))

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
    order_type = 'callback_req'
    send_order_status = False
    send_client_status = False

    async def get(self, request):
        try:
            pass
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'CallbackRequestView')
        
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)
    
    async def post(self, request):
        try:
            req_body = json.loads(request.body)
            order = await generate_order_number('consult', 1)
            not_format_date = order.get('not_format_date')
            time = order.get('order_date')
            order_number = order.get('order_number')
            email_data = {
                'phone': req_body.get('phone'),
                'time': req_body.get('time'),
                'type': req_body.get('type'),
            }

            if email_data.get('phone'):
                email_template = await select_email_template_by_order(self.order_type)
                response_description = email_template.get('response_description')
                
                await CallbackRequests.objects.acreate(
                    phone = email_data.get('phone'),
                    name = '',
                    request_time = not_format_date
                )
                self.send_order_status = True
                
                return Response(
                    {'message': 'ok', 'description': response_description}, 
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'message': 'err phone not valid'}, 
                status=status.HTTP_200_OK
            )

        except Exception as err:
            method = request.method
            create_err_log = await write_access_view_err_log(err, method, 'CallbackRequestView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            await create_err_log
            
            return Response(
                {'message': 'ok', 'description': err_description}, 
                status=status.HTTP_200_OK
            )
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, email_data, time, order_number)
    
class RequestConsultView(APIView):

    permission_classes = [IsAuthenticated, ]
    order_type = 'consult_req'
    send_order_status = False
    send_client_status = False

    async def post(self, request):
        try:
            req_body = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('consult', 1)
            not_format_date = order.get('not_format_date')
            time = order.get('order_date')
            order_number = order.get('order_number')
            response_description = email_template.get('response_description')
            consult_data = {
                'name': req_body.get('name'),
                'phone': req_body.get('phone'),
                'email': req_body.get('email'),
                'city': req_body.get('city'),
                'comment': req_body.get('comment'),
            }

            if not consult_data.get('email') and not consult_data.get('phone'):
                return Response({'status': 'not found', 'description': 'email or phone not valid'}, status=status.HTTP_200_OK)
        
            async for client in Client.objects.filter(Q(email=consult_data['email']) | Q(phone=consult_data['phone'])):
                check_client = client

            if not check_client.name:
                await Client.objects.acreate(
                    name=consult_data.get('name'), 
                    phone=consult_data.get('phone'), 
                    email=consult_data.get('email'),
                )

            await ConsultRequest.objects.acreate(
                name=consult_data.get('name'), 
                phone=consult_data.get('phone'), 
                email=consult_data.get('email'),
                city=consult_data.get('city'),
                comment=consult_data.get('comment'),
                request_time = not_format_date
            )

            client_data = {
                'client_name': consult_data.get('name'),
                'client_phone': consult_data.get('phone'),
                'client_email': consult_data.get('email'),
                'client_city': consult_data.get('city'),
                'call_option': '',
                'order_type_name': 'Консультация',
                'client_comment': consult_data.get('comment'),
            }
            self.send_order_status = True

            if validate_email(client_data.get('client_email')):
                self.send_client_status = True
                client_template = await select_client_email_template_by_order(self.order_type)
        
            return Response(
                {'message': 'ok', 'description': response_description}, 
                status=status.HTTP_201_CREATED
            )
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'RequestConsultView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response(
                {'message': 'ok', 'description': err_description}, 
                status=status.HTTP_200_OK
            )
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, client_data, time, order_number)
            if self.send_client_status:
                await send_email_to_client(
                    client_template,
                    client_data.get('client_name'),  
                    client_data.get('client_email'), 
                    order
                )

class RequestOrderView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'order_req'
    send_order_status = False
    send_client_status = False
    
    async def post(self, request):
        try:
            req_body = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            response_description = email_template.get('response_description')
            order_data = {
                "name": req_body.get('name'),
                "email": req_body.get('email'),
                "phone": req_body.get('phone'),
                "comment": req_body.get('comment'),
                "options": req_body.get('options')
            }
        
            if not order_data.get('email') and not order_data.get('phone'):
                return Response({'status': 'not found', 'description': 'email or phone not valid'}, status=status.HTTP_200_OK)
            
            if order_data.get('email') or order_data.get('phone'):
                target_client = await find_existing_data_by_contact(Client, order_data.get('phone'), order_data.get('email'))
            else:
                await Client.objects.acreate(
                    name = order_data.get('name'),
                    email = order_data.get('email'),
                    phone = order_data.get('phone'),
                )
                target_client = await Client.objects.aget(
                    name = order_data.get('name'),
                    email = order_data.get('email'),
                    phone = order_data.get('phone'),
                )

            if not order_data.get('options'):
                order_data['options'] = 'Расчет контрактного производства'

            order = await generate_order_number('contract', target_client.id)
            order_obj = await Order.objects.acreate(
                order_type=order.get('order_number'), 
                order_date=order.get('not_format_date')
            )

            await ClientOrder.objects.acreate(
                client_id=target_client, 
                order_id=order_obj,
                order_number = order.get('order_number'), 
                order_date = order.get('date'),
                oreder_description = order_data.get('comment'),
                order_option = order_data.get('options')
            )

            not_format_date = datetime.now()
            time = get_time(not_format_date)
            client_data = {
                'client_name': order_data.get('name'),
                'client_phone': order_data.get('phone'),
                'client_email': order_data.get('email'),
                'order_number': order.get('order_number'),
                'call_option': 'Любой',
                'order_type_name': order_data.get('options'),
                'client_comment': order_data.get('comment'),
            }
            self.send_order_status = True

            if validate_email(client_data.get('client_email')):
                self.send_client_status = True
                client_email_template = await select_client_email_template_by_order(self.order_type)

            return Response(
                {'message': 'ok', 'description': f"{response_description} {client_data.get('order_number')}"}, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'RequestOrderView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'
            
            return Response({'message': 'ok', 'description': err_description}, status=status.HTTP_201_CREATED)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, client_data, time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    client_data.get('client_name'),
                    client_data.get('client_email'),  
                    order
                )
    
class ContactsRequestView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'contacts_order_req'
    send_order_status = False
    send_client_status = False

    async def post(self, request):
        try:
            req_body = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
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
        
            if contacts_data.get('orderType') in order_types and contacts_data.get('orderType') not in order_cooperations:
                target_client = await find_existing_data_by_contact(Client, contacts_data.get('phone'), contacts_data.get('email'))
                order = await generate_order_number('contract', target_client.id)
                time = order.get('order_date')
                
                if not target_client:
                    Client.objects.acreate(
                        name=contacts_data.get('name'), 
                        phone=contacts_data.get('phone'), 
                        email=contacts_data.get('email'),
                    )
                    target_client = Client.objects.aget(
                        name=contacts_data.get('name'), 
                        phone=contacts_data.get('phone'), 
                        email=contacts_data.get('email')
                    )

                order_obj = await Order.objects.acreate(
                    order_type=order.get('order_number'), 
                    order_date=order.get('not_format_date')
                )

                await ClientOrder.objects.acreate(
                    client_id=target_client, 
                    order_id=order_obj,
                    order_number = order.get('order_number'), 
                    order_date = order.get('date'),
                    oreder_description = contacts_data.get('comment'),
                    order_option = contacts_data.get('orderType'),
                )

                if contacts_data.get('file') and len(contacts_data.get('file')) > 0:
                    files_list = contacts_data.get('file')
                    target_order = await ClientOrder.objects.aget(order_number=order.get('order_number'))
               
                    for file in files_list:
                        file_path = await create_file(file, settings.ORDER_FILES)
                        await ClientOrderFile.objects.acreate(client_order=target_order, file=file_path,)
                        client_files.append(file_path)
            
                client_data = {
                    'client_name': contacts_data.get('name'),
                    'client_phone': contacts_data.get('phone'),
                    'client_email': contacts_data.get('email'),
                    'client_city': contacts_data.get('city'),
                    'call_option': get_request_name(contacts_data.get('call_option')),
                    'client_comment': contacts_data.get('comment'),
                    'order_number': order.get('order_number'),
                    'order_type': order.get('type'),
                    'order_type_name': get_request_name(contacts_data.get('orderType')),
                }
                client_data['files'] = client_files
                response_description = email_template.get('response_description')
                self.send_order_status = True

                if validate_email(client_data.get('client_email')):
                        self.send_client_status = True
                        client_email_template = await select_client_email_template_by_order(self.order_type)

                return Response(
                    {'message': 'ok', 'description': f"{response_description} {order.get('order_number')}"}, 
                    status=status.HTTP_201_CREATED
                )
        
            elif contacts_data.get('orderType') in order_cooperations and contacts_data.get('orderType') not in order_types:
                self.order_type = 'contacts_coperation_req'
                email_template = await select_email_template_by_order(self.order_type)
                order = await generate_order_number('cooperation', 1)
                time = order.get('order_date')

                if contacts_data.get('phone') or contacts_data.get('email'):
                    cooperation_request = await find_existing_data_by_contact(CoperationRequest, contacts_data.get('phone'), contacts_data.get('email'))

                    if not cooperation_request.id:
                        cooperation_request = await CoperationRequest.objects.acreate(
                            name = contacts_data.get('name'),
                            email = contacts_data.get('email'),
                            phone = contacts_data.get('phone'),
                            request_description = contacts_data.get('comment'),
                            cooperation_type = contacts_data.get('orderType'),
                        )

                    if contacts_data.get('file') and len(contacts_data.get('file')) > 0:
                        files_list = contacts_data.get('file')
                        target_cooperation = await CoperationRequest.objects.aget(id=cooperation_request.id)
                        for file in files_list:
                            file_path = await create_file(file, settings.COOPERATION_FILES)
                            await CoperationRequestFile.objects.acreate(
                                cooperation_request_id=target_cooperation, 
                                file=file_path,
                            )
                            cooperation_files.append(file_path)

                    client_data = {
                        'client_name': contacts_data.get('name'),
                        'client_phone': contacts_data.get('phone'),
                        'client_email': contacts_data.get('email'),
                        'client_city': contacts_data.get('city'),
                        'call_option': get_request_name(contacts_data.get('call_option')),
                        'order_type_name': get_request_name(contacts_data.get('orderType')),
                        'client_comment': contacts_data.get('comment'),
                    }
                    client_data['files'] = cooperation_files
                    response_description = email_template.get('response_description')
                    self.send_order_status = True

                    if validate_email(client_data.get('client_email')):
                        self.send_client_status = True
                        client_email_template = await select_client_email_template_by_order(self.order_type)

                    return Response(
                        {'message': 'ok', 'description': f"{response_description}"}, 
                        status=status.HTTP_201_CREATED
                    )
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'message': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'
            await write_access_view_err_log(err, method, 'ContactsRequestView')
          
            
            return Response({'message': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, client_data, time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    client_data.get('client_name'),
                    client_data.get('client_email'),  
                    order
                )

class CityDataView(APIView):

    permission_classes = [IsAuthenticated, ]

    async def get(self, request):
        try:
            params = request.query_params
            city_param = params.get('city')

            if not city_param:
                all_cities = await get_all_data_from_model(CityData)

                return Response({'cities': all_cities}, status=status.HTTP_200_OK)

            check_dach = re.search('-', city_param)
            format_city_name = f'{city_param[0].upper()}{city_param[1:len(city_param)]}'
        
            if check_dach:
                name_part = city_param.split('-')
                format_city_name = f'{name_part[0][0].upper()}{name_part[0][1:len(name_part[0])]}-{name_part[1][0].upper()}{name_part[1][1:len(name_part[1])]}'

            # city_name = fr'^{format_city_name}|^{format_city_name}(\w*|.*)(.|\w)(\w+)$'
            target_city = await CityData.objects.aget(name=format_city_name)

            return Response({'cities': [model_to_dict(target_city)]}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'CityDataView')
            
            return Response({'cities': {}, 'err': err}, status=status.HTTP_400_BAD_REQUEST)

class QuizOrderView(APIView):

    permission_classes = [IsAuthenticated, ]
    order_type = 'quiz_req'
    send_order_status = False
    send_client_status = False
    
    async def post(self, request):
        try:
            req_body = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            client_name = req_body.get('name').get('value')
            client_phone = req_body.get('phone').get('value')
            client_email = req_body.get('email').get('value')
            send_data = req_body.get('sendData')
            order_data = dict()
            upload_folder = f'{os.getcwd()}/upload_files/quiz_files/'
            order = await generate_order_number('quiz', 1)
            time =  order.get('order_date')
            order_folder_name = f"quiz_{order.get('order_number')}"
            order_folder_path = f'{upload_folder}{order_folder_name}/'
            send_description = {
                'title': f'Спасибо за обращение {client_name}',
                'order': order.get('order_number'),
                'description': 'Наш сотрудник пришлет рассчет/свяжется с вами в билижайшее время'
            }

            if not client_email or not client_phone:
                send_description = {
                    'title': f'Спасибо за обращение!',
                    'order': '',
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
                custom_tz_file_url = await create_file(custom_tz_file, order_folder_path)
            
            if custom_package_file != 'empty':
                custom_package_file_url = await create_file(custom_package_file, order_folder_path)


            await QuizOrder.objects.acreate(
                order_number=order.get('order_number'),
                order_date=order.get('not_format_date'),
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
                'order_number': order.get('order_number'),
                'order_date':  time,
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
            if email_data.get('custom_tz_file') or email_data.get('custom_package_file'):
                email_data['files'] = [email_data.get('custom_tz_file'), email_data.get('custom_package_file')]
            self.send_order_status = True

            if validate_email(email_data.get('client_email')):
                self.send_client_status = True
                client_email_template = await select_client_email_template_by_order(self.order_type)

            return Response({'status': 'ok', 'created': True, 'message': send_description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'QuizOrderView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'
            
            return Response({'status': 'ok', 'created': True, 'message': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, email_data, time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    email_data.get('client_name'),
                    email_data.get('client_email'),
                    order
                )

class QuestionOrderView(APIView):

    permission_classes = [IsAuthenticated, ]
    order_type = 'question_req'
    send_order_status = False
    send_client_status = False

    async def post(self, request):
        try:
            req_body = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('quiz_consult', 1)
            time = order.get('order_date')
            client_name = req_body.get('name')
            client_phone = req_body.get('phone')
            client_email = req_body.get('email')
            client_question = req_body.get('comment')
            client_communication_type = req_body.get('communicationType')
            send_description = {
                'title': f'Спасибо за обращение {client_name}',
                'order': order.get('order_number'),
                'description': 'Наш сотрудник свяжется с вами в течении 30 минут'
            }

            if not (client_phone or client_email):
                send_description = {
                    'title': f'Спасибо за обращение {client_name}',
                    'order': '',
                    'description': 'Произошла ошибка, попробуйте позднее, либо напишите запрос на pro@cosmtech.ru'
                }
                return Response({'status': 'err', 'created': False, 'message': send_description}, status=status.HTTP_200_OK)
        
            await QuizQuestionOrder.objects.acreate(
                order_number = order.get('order_number'),
                order_date = order.get('not_format_date'),
                client_name = client_name,
                client_phone = client_phone,
                client_email = client_email,
                communication_type = client_communication_type,
                client_question = client_question,
            )
            email_data = {
                'order_type_name': 'Задать вопрос технологу',
                'order_number': order.get('order_number'),
                'order_date':  time,
                'client_name': client_name,
                'client_phone': client_phone,
                'client_email': client_email,
                'communication_type': client_communication_type,
                'client_question': client_question
            }
            self.send_order_status = True

            if validate_email(email_data.get('client_email')):
                self.send_client_status = True
                client_email_template = await select_client_email_template_by_order(self.order_type)

            return Response({'status': 'ok', 'created': True, 'message': send_description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'QuestionOrderView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'status': 'ok', 'created': True, 'message': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, email_data, time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    email_data.get('client_name'),
                    email_data.get('client_email'),
                    order
                )
    
class TzOrderView(APIView):

    permission_classes = [IsAuthenticated, ]
    order_type = 'tz_req'
    send_order_status = False
    send_client_status = False

    async def post(self, request):
        try:
            req_body = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('quiz_tz', 1)
            not_format_date = order.get('not_format_date')
            order_time = order.get('order_date')
            upload_folder = f'{os.getcwd()}/upload_files/quiz_files/'
            order_folder_name = f"tz_{order.get('order_number')}"
            order_folder_full_path = f'{upload_folder}{order_folder_name}/'
            client_name = req_body.get('name')
            client_phone = req_body.get('phone')
            client_email = req_body.get('email')
            client_tz_file = req_body.get('file')
            send_description = {
                'title': f'Спасибо за обращение {client_name}',
                'order': order.get('order_number'),
                'description': 'Наш сотрудник свяжется с вами в течении 30 минут'
            }

            if not client_tz_file:
                send_description = {
                    'title': f'Спасибо за обращение {client_name}',
                    'order': order.get('order_number'),
                    'description': 'Произошла ошибка, попробуйте позднее, либо отправьте тз на pro@cosmtech.ru'
                }
                return Response({'status': 'err', 'created': False, 'message': send_description}, status=status.HTTP_200_OK)
            
            if not os.path.exists(f'{order_folder_full_path}'):
                os.mkdir(f'{order_folder_full_path}')
            tz_file_url = await create_file(client_tz_file, f'{order_folder_full_path}')

            await QuizTzOrder.objects.acreate(
                order_number = order.get('order_number'),
                order_date = not_format_date,
                client_name = client_name,
                client_phone = client_phone,
                client_email = client_email,
                tz_file = tz_file_url,
            )
            email_data = {
                'order_type_name': 'Техническое Задание',
                'order_number': order.get('order_number'),
                'order_date': order_time,
                'client_name': client_name,
                'client_phone': client_phone,
                'client_email': client_email,
                'tz_file': tz_file_url,
            }

            email_data['file'] = email_data.get('tz_file')
            self.send_order_status = True

            if validate_email(email_data.get('client_email')):
                self.send_client_status = True
                client_email_template = await select_client_email_template_by_order(self.order_type)
            
            return Response({'status': 'ok', 'created': True, 'message': send_description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'TzOrderView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'status': 'ok', 'created': True, 'message': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, email_data, order_time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    email_data.get('client_name'),
                    email_data.get('client_email'),
                    order
                )
    
class VacancyView(APIView):

    permission_classes = [IsAuthenticated, ]
    order_type = 'vacancy_req'
    send_order_status = False
    send_client_status = False

    async def get(self, request):
        try:
            vacancy_data = await get_all_data_from_model(Vacancy)
            data = [
                { 
                    'id': vacancy_obj.get('id'),
                    'date':  get_time(vacancy_obj.get('open_date')),
                    'name': vacancy_obj.get('name'),
                    'departament': vacancy_obj.get('departament'),
                    'salary': vacancy_obj.get('salary'),
                    'phone': vacancy_obj.get('contact_phone'),
                    'requirements': filter(lambda item: (item != '') , vacancy_obj.get('requirements').split(';')),
                    'conditions': filter(lambda item: (item != ''), vacancy_obj.get('conditions').split(';')),
                    'dutys': filter(lambda item: (item != ''), vacancy_obj.get('dutys').split(';')),
                } 
                for vacancy_obj in vacancy_data
            ]

            return Response({'vacancy': data}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'TzOrderView')

            return Response({'status': 'err', 'message': err}, status=status.HTTP_400_BAD_REQUEST)
    
    async def post(self, request):
        try:
            send_data = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('vacancy_req', 1)
            order_time = order.get('order_date')
            vacancy_data = {
                'resume_name': send_data.get('name'),
                'resume_phone': send_data.get('phone'),
                'resume_file': send_data.get('file'),
                'vacancy_data': send_data.get('vacancy')
            }

            if not vacancy_data.get('resume_phone'):
                return Response({'status': 'err'})
            
            resume_folder_name = f"{vacancy_data.get('resume_name')}_{vacancy_data.get('vacancy_data')}_{vacancy_data.get('resume_phone')}"
            upload_folder = f'{os.getcwd()}/upload_files/resume_files/'
            resume_folder_full_path = f'{upload_folder}{resume_folder_name}/'
            file = ''

            if vacancy_data.get('resume_file'):
                if not os.path.exists(resume_folder_full_path):
                    os.mkdir(resume_folder_full_path)
                vacancy_data['resume_file'] = await create_file(vacancy_data.get('resume_file'), resume_folder_full_path)
        
            response_data = {
                'title': f"Спасибо {vacancy_data['resume_name']}, Ваш отклик очень важен для нас!",
                'description': 'Специалисты свяжутся с вами по телефону в ближайшее время.'
            }
            if vacancy_data.get('resume_file'):
                vacancy_data['files'] = [vacancy_data.get('resume_file')]
            self.send_order_status = True

            return Response({'status': 'ok', 'data': response_data}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            response_data = {
                'title': f"Спасибо ваш отклик очень важен для нас!",
                'description': 'Что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'
            }
            await write_access_view_err_log(err, method, 'VacancyView')

            return Response({'status': 'err', 'message': err, 'data': response_data}, status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, vacancy_data, order_time, order.get('order_number'))

    
class SupplierView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    async def get(self, request):
        try:
            query_suppliers = await get_all_data_from_model(Supplier)
            query_suppliers_types = await get_all_data_from_model(SupplierType)

            for suplier in query_suppliers:
                suplier['type'] = list(filter(lambda supl_type: supl_type.get('id') == suplier.get('type_id'), query_suppliers_types))[0].get('name')
            
            return Response({'status': 'ok', 'data': query_suppliers}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'SupplierView')

            return Response({'status': 'err', 'data': [], 'description': err }, status=status.HTTP_400_BAD_REQUEST)

class SuppliersTypeView(APIView):
    permission_classes = [IsAuthenticated, ]

    async def get(self, request):
        try:
            query_suppliers_types = await get_all_data_from_model(SupplierType)

            return Response({'status': 'ok', 'data': query_suppliers_types}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'SuppliersTypeView')

            return Response({'status': 'err', 'data': [], 'description': err}, status=status.HTTP_200_OK)
    
class ForClientsRequestView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'for_clients_req'
    send_order_status = False
    send_client_status = False

    async def post(self, request):
        try:
            req_data = json.loads(json.dumps(request.data))
            email_data = dict()
            order = await generate_order_number('supl_consult', 1)
            order_time = order.get('order_date')
            description = f'спасибо ваш запрос зарегистрирован, менеджер свяжется с вами в ближайшее время'
            client_data = {
                'request_type': req_data.get('requestType'),
                'name': req_data.get('name'),
                'phone': req_data.get('phone'),
                'email': req_data.get('email'),
                'comment': req_data.get('comment'),
            }

            if not client_data.get('phone') and not client_data.get('email'):
                return Response({'status': 'err', 'message': 'phone or email not found'}, status=status.HTTP_200_OK)
        
           
            if client_data.get('request_type') and client_data.get('request_type') == 'suplconsult':
                self.order_type = 'for_clients_supl_req'
                email_data['order_type'] = client_data.get('request_type')
                email_data['order_type_name'] = 'Вопрос по поставщикам'
                email_data['client_name'] = client_data.get('name')
                email_data['client_phone'] = client_data.get('phone')
                description = f'Спасибо за ваше обращение {"".join(str(email_data["client_name"]))} менеджер свяжется с вами в течении 30 мин.'
                email_data['description'] = description

            elif client_data.get('request_type') and client_data.get('request_type') == 'prodquestion':
                self.order_type = 'for_clients_prod_req'
                email_data['order_type'] = client_data.get('request_type')
                email_data['order_type_name'] = 'Вопрос по работе производства'
                email_data['client_name'] = client_data.get('name')
                email_data['client_email'] = client_data.get('email')
                email_data['comment'] = client_data.get('comment')
                description = f'Спасибо за ваше обращение {"".join(str(email_data["client_name"]))} менеджер свяжется с вами в течении 30 мин.'
                email_data['description'] = description

            elif (not client_data.get('request_type') and client_data.get('email')) or (not client_data.get('request_type') and client_data.get('phone')):
                email_data = {
                    'order_type_name': 'empty',
                    'client_name': client_data.get('name'),
                    'client_phone': client_data.get('phone'),
                    'client_email': client_data.get('email'),
                    'comment': client_data.get('comment'),
                }
            email_template = await select_email_template_by_order(self.order_type)
            self.send_order_status = True

            if validate_email(email_data.get('client_email')):
                self.send_client_status = True
                client_email_template = await select_client_email_template_by_order(self.order_type)

            return Response({'status': 'ok', 'description': description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'ForClientsRequestView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'status': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, email_data, order_time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    email_data.get('client_name'),
                    email_data.get('client_email'),
                    order
                )
    
class ExcursionProductionView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'excursion_req'
    send_order_status = False
    send_client_status = False

    async def get(self, request):

        return Response({'status': 'ok'})
    
    async def post(self, request):
        try:
            data = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('excursion_req', 1)
            cleint_name = data.get('name')
            client_phone = data.get('phone')
            excursion_data = data.get('date')
            excursion_time = data.get('time')
            order_number = order.get('order_number')
            order_time = order.get('order_date')
            client_data = dict()

            if not cleint_name or not client_phone or not excursion_data or not excursion_time:
                return Response({'status': 'err', 'description': 'send data err'}, status=status.HTTP_200_OK)
        
            send_description = {
                'title': 'Спасибо, Ваш запрос на экскурсию принят!',
                'order': order_number,
                'description': f'Желаемая дата визита: {excursion_data} в {excursion_time}'
            }
            valid_date = dt.datetime.strptime(re.sub(r'[-]', '/', excursion_data), "%Y/%m/%d").strftime('%Y-%m-%d')
            valid_time = dt.time(int(excursion_time[:2]), int(excursion_time[3:]), 00) 
        
            await ExcursionProductionRequest.objects.acreate(
                excursion_number = order_number,
                client_name = cleint_name,
                client_phone = client_phone,
                excursion_date = valid_date,
                excursion_time = valid_time
            )

            client_data['order_number'] = order_number
            client_data['name'] = cleint_name
            client_data['client_phone'] = client_phone
            client_data['excursion_data'] = excursion_data
            client_data['excursion_time'] = excursion_time

            self.send_order_status = True

            return Response({'status': 'ok', 'description': send_description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'ExcursionProductionView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'status': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, client_data, order_time, order.get('order_number'))

    
class DecorativeCosmeticView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'decorative_cosm_req'
    send_order_status = False
    send_client_status = False

    async def post(self, request):
        try:
            send_data = json.loads(json.dumps(request.data))
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('contract_decorative', 1)
            order_time = order.get('order_date')
            client_name = send_data.get('name')
            client_phone = send_data.get('phone')
            client_email = send_data.get('email')
            client_comment = send_data.get('comment')
            file_obj = send_data.get('fileData')
            request_type = send_data.get('reqType')
            client_data = dict()
            description = dict()

            client_data['client_name'] = client_name
            client_data['client_phone'] = client_phone
            client_data['client_email'] = client_email
        
            if request_type == 'consult':
                description['title'] = 'Спасибо! Ваш запрос отправлен!'
                description['description'] = 'Менеджер свяжется с вами в течении 30 минут.'

                client_data['order_type'] = 'decorative_consult'
                client_data['order_type_name'] = 'Декоративная косметика консультация'
                self.send_order_status = True

                if validate_email(client_data.get('client_email')):
                    self.send_client_status = True
                    client_email_template = await select_client_email_template_by_order(self.order_type)

                return Response({'status': 'ok', 'description': description}, status=status.HTTP_201_CREATED)
        
            if request_type == 'order':
                client_data['order_type_name'] = 'Декоративная косметика запрос рассчета'
                description['title'] = 'Спасибо! Ваш запрос отправлен!'
                description['description'] = 'Менеджер свяжется с вами в течении 30 минут.'
                description['order'] = ''
                client_files = []
                target_client = await find_existing_data_by_contact(Client, client_data.get('client_phone'), client_data.get('client_email'))

                if not target_client:
                    await Client.objects.acreate(
                        name=client_name, 
                        phone=client_phone, 
                        email=client_email,
                    )
                    target_client = await find_existing_data_by_contact(Client, client_data.get('client_phone'), client_data.get('client_email'))
                    
                order = await generate_order_number('contract_decorative', target_client.id)
                order_obj = await Order.objects.acreate(
                    order_type=order.get('order_number'), 
                    order_date=order.get('not_format_date')
                )
                description['order'] = order.get('order_number')

                await ClientOrder.objects.acreate(
                    client_id=target_client, 
                    order_id=order_obj,
                    order_number = order.get('order_number'), 
                    order_date = order.get('date'),
                    oreder_description = client_comment,
                    order_option = client_data.get('order_type_name'),
                    file = 'test'
                )

                if file_obj and file_obj.get('file') and file_obj.get('type'):
                    file_path = await create_file(file_obj, settings.ORDER_FILES)
                    target_order = await ClientOrder.objects.aget(order_number=order.get('order_number'))
                    await ClientOrderFile.objects.acreate(client_order=target_order, file=file_path,)
                    client_files.append(file_path)

                client_data = {
                    'client_name': client_name,
                    'client_phone': client_phone,
                    'client_email': client_email,
                    'client_city': '',
                    'call_option': '',
                    'client_comment': client_comment,
                    'order_number': order.get('number'),
                    'order_type': order.get('type'),
                    'order_type_name': get_request_name('decor'),
                }
                client_data['files'] = client_files
                self.send_order_status = True

                if validate_email(client_data.get('client_email')):
                    self.send_client_status = True
                    client_email_template = await select_client_email_template_by_order('decorative_cosm_req_order')
                
                return Response({'status': 'ok', 'description': description}, status=status.HTTP_201_CREATED)
            
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'DecorativeCosmeticView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'status': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, client_data, order_time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    client_data.get('client_name'),
                    client_data.get('client_email'),
                    order
                )

class SpecForProductionView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'specification_req'
    send_order_status = False
    send_client_status = False

    async def get(self, request):
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

    async def post(self, request):
        try:
            send_data = json.loads(json.dumps(request.data))
            happy_state_description = dict()
            email_template = await select_email_template_by_order(self.order_type)
            order = await generate_order_number('tz_cosm', 1)
            order_time = order.get('order_date')

            specification_data = await create_specification_file(send_data)
            specification_data['client_email'] = send_data.get('customerEmail')
            specification_data['client_name'] = send_data.get('customerName')
            specification_data['client_phone'] = send_data.get('customerPhone')
            specification_data['client_city'] = send_data.get('customerCity')
            specification_data['package_type'] = send_data.get('packageType')
            specification_data['package_body'] = send_data.get('packageCategory')
            specification_data['package_head'] = send_data.get('packageName')
            specification_data['custom_package'] = send_data.get('packageForUser')
            specification_data['product_type'] = send_data.get('productType')
            specification_data['product_category'] = send_data.get('productCategory')
            specification_data['product_name'] = send_data.get('productName')
            specification_data['product_params'] = send_data.get('productParams')
            specification_data['product_size'] = send_data.get('productSize')
            specification_data['product_segment'] = send_data.get('productSegment')
            specification_data['services'] = ', '.join(i for i in send_data.get('services') if len(send_data.get('services')) > 0)
            specification_data['delivery'] = send_data.get('delivery')
            specification_data['quantity'] = send_data.get('quantity')
            specification_data['product_example_url'] = send_data.get('productExampleUrl')
            specification_data['product_example_file'] = {
                'name': send_data.get('productExampleFile').get('name'),
                'type': send_data.get('productExampleFile').get('type'),
                'file': send_data.get('productExampleFile').get('fileData'),
                'path': ''
            }
            if specification_data['product_example_file']['file'] and specification_data['product_example_file']['name']:
                specification_data['product_example_file']['path'] = await create_file(
                    specification_data['product_example_file'], 
                    specification_data.get('tmp_file_path')
                )

            if not specification_data or not specification_data['tmp_file_path']:
                happy_state_description['title'] = 'Что-то пошло не так'
                happy_state_description['description'] = 'Проверье все поля или отправьте запрос на pro@cosmtech.ru, указав что получили ошибку при формировании тз'

                return Response({'status': 'err', 'description': happy_state_description}, status=status.HTTP_200_OK)
        
            await SpecificationOrder.objects.acreate(
                order_date = datetime.now(),
                order_number = specification_data.get('order_number'),
                client_name = specification_data.get('client_name'),
                client_email = specification_data.get('client_email'),
                client_phone = specification_data.get('client_phone'),
                client_city = specification_data.get('client_city'),
                product_type = specification_data.get('product_type'),
                product_category = specification_data.get('product_category'),
                product_name = specification_data.get('product_name'),
                product_params =specification_data.get('product_params'),
                product_segment = specification_data.get('product_segment'),
                product_example_url = specification_data.get('product_example_url'),
                product_size = specification_data.get('product_size'),
                package_type = specification_data.get('package_type'),
                package_body = specification_data.get('package_body'),
                package_head = specification_data.get('package_head'),
                custom_package = specification_data.get('custom_package'),
                services = specification_data.get('services'),
                delivery = specification_data.get('delivery'),
                quantity = int(specification_data.get('quantity')),
                tz_file_path =  specification_data.get('tmp_file_path'),
                product_example_file = specification_data['product_example_file']['path']
            )
            if specification_data.get('tmp_file_path'):
                specification_data['files'] = [specification_data.get('tmp_file_path')]

            if specification_data['product_example_file']['path']:
                specification_data['files'].append(specification_data['product_example_file']['path'])
            self.send_order_status = True

            if validate_email(specification_data.get('client_email')):
                self.send_client_status = True
                client_email_template = await select_client_email_template_by_order(self.order_type)
        
            happy_state_description['title'] = f"Спасибо, за обращене {specification_data['client_name']}!"
            happy_state_description['description'] = f"Ваше ТЗ № {specification_data['order_number']} отправлено, мы выйдем на связь в ближайшее время."

            return Response({'status': 'ok', 'description': happy_state_description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'SpecForProductionView')
            err_description = 'Очень жаль, но что-то пошло не так, отправьте запрос вручную на pro@cosmtech.ru'

            return Response({'status': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
        finally:
            if self.send_order_status:
                await send_order_to_main_email(email_template, specification_data, order_time, order.get('order_number'))
            if self.send_client_status:
                await send_email_to_client(
                    client_email_template, 
                    specification_data.get('client_name'),
                    specification_data.get('client_email'),
                    order
                )
class ArticlesView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'articles'

    async def post(self, request):
        try:
            params = dict(request.query_params)
            send_data = json.loads(json.dumps(request.data))
            email_data = dict()
            happy_state_description = dict()
            
            is_form = params.get('sendform')

            if is_form and send_data.get('phone') and is_form[0]:
                self.order_type = 'article_inner_form'
                email_template = await select_email_template_by_order(self.order_type)
                order = await generate_order_number('consult', 1)
                order_time = order.get('order_date')

                contact_types = [
                    {'name': 'contactPhone', 'value': 'Телефон'},
                    {'name': 'contactWp', 'value': 'Whatsapp'},
                    {'name': 'contactTg', 'value': 'Telegram'},
                ]
                email_data['client_name'] = send_data.get('name')
                email_data['client_phone'] = send_data.get('phone')
                email_data['client_question'] = send_data.get('comment')
                email_data['contact_type'] = send_data.get('contactType')
                email_data['article'] = send_data.get('articleName')
                
                for contact_type in contact_types:
                    if contact_type['name'] == email_data.get('contact_type'):
                        email_data['contact_type'] = contact_type['value']

                tmp_str = f"{email_data.get('client_name')}! Номер обращения: № {order.get('order_number')}"
                happy_state_description['title'] = f"{email_template.get('response_title')}!"
                happy_state_description['description'] = f"{email_template.get('response_description')}." + tmp_str

                await send_order_to_main_email(email_template, email_data, order_time, order.get('order_number'))
                
                return Response({'status': 'ok', 'description': happy_state_description}, status=status.HTTP_201_CREATED)
            return Response({'status': 'ok', 'description': ''}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'ArticlesViewFrom')
            happy_state_description = {
                'title': 'Очень жаль, но что-то пошло не так',
                'description': f"отправьте пожалуйста запрос вручную на pro@cosmtech.ru"
            }

            return Response({'status': 'ok', 'description': happy_state_description}, status=status.HTTP_200_OK)
        

class NewsView(APIView):
    permission_classes = [IsAuthenticated, ]
    order_type = 'news'

    async def get(self, request):
        try:
            current_date = dt.date.today()
            prev_date = dt.date.today()-dt.timedelta(1)
            await get_currency_daily_course(current_date, prev_date)
            all_news = []
            async for news_item in NewsItem.objects.all():
                news_obj = dict()
                news_obj['urls'] = []
                news_obj['videos'] = []
                news_obj['banners'] = []
                
                async for url_item in news_item.news_url.all().values():
                    news_obj['urls'].append(url_item)
                async for banner_item in news_item.news_image.all().values():
                    banner_file = await file_to_base64(banner_item['news_image'])
                    if banner_file:
                        news_obj['banners'].append({**banner_item, 'banner_file': banner_file})
                    else:
                        news_obj['banners'].append({**banner_item, 'banner_file': ''})

                async for video_item in news_item.news_video.all().values():
                    video_file = await file_to_base64(video_item['file'])
                    if video_file:
                        news_obj['videos'].append({**video_item, 'video_file': video_file})
                    else:
                        news_obj['videos'].append({**video_item, 'video_file': ''})
                        
                news_obj['id'] = news_item.id
                news_obj['title'] = news_item.title
                news_obj['date'] = news_item.date
                news_obj['min_img'] = await file_to_base64(news_item.min_img)
                news_obj['min_img_alt'] = news_item.min_img_alt
                news_obj['short_description'] = news_item.short_description
                news_obj['text_content'] = await get_paragraphs_from_text(news_item.text_content)

                all_news.append(news_obj)

            return Response({'status': 'ok', 'news': all_news}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'NewsView')
            err_description = 'Ошибка доступа к новостям'

            return Response({'status': 'ok', 'description': err_description}, status=status.HTTP_200_OK)
        
    async def post(self, request):
        try:
            params = dict(request.query_params)
            send_data = json.loads(json.dumps(request.data))
            email_data = send_data.get('sendData')
            is_form = params.get('sendform')

            if is_form and email_data.get('phone') and is_form[0]:
                self.order_type = 'news_form_req'
                email_template = await select_email_template_by_order(self.order_type)
                order = await generate_order_number('consult', 1)
                order_time = order.get('order_date')

                email_data['client_name'] = email_data.get('name')
                email_data['client_phone'] = email_data.get('phone')
                email_data['client_question'] = email_data.get('comment')
                happy_state_description = {
                    'title': f"Спасибо за обращение {email_data.get('client_name')}!",
                    'description': f"{email_template.get('response_description')} №{order.get('order_number')} отправлен"
                }

                # await send_order_to_main_email(email_template, email_data, order_time, order.get('order_number'))
                
            return Response({'status': 'ok', 'description': happy_state_description}, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'NewsViewFrom')
            happy_state_description = {
                'title': 'Очень жаль, но что-то пошло не так',
                'description': f"отправьте пожалуйста запрос вручную на pro@cosmtech.ru"
            }

            return Response({'status': 'ok', 'description': happy_state_description}, status=status.HTTP_200_OK)
        
class CurrencyCourseView(APIView):

    async def get(self, request):
        try:
            param = request.GET.get('name')
            json_path = f'{os.getcwd()}/upload_files/news_files/currency/currency.json'

            if not (os.path.exists(json_path)):
                return Response({'status': 'ok', 'data': []}, status=status.HTTP_200_OK)
            
            
            result_data = await read_json_file_by_parh(json_path)

            if bool(param):
                result_data = list(filter(lambda x: x['char_code'] == str(param), result_data))
                return Response({'status': 'ok', 'data': result_data}, status=status.HTTP_200_OK)


            return Response({'status': 'ok', 'data': result_data}, status=status.HTTP_200_OK)
        
        except Exception as err:
            method = request.method
            await write_access_view_err_log(err, method, 'CurrencyCourseView')

@sync_to_async
@api_view(['GET'])
def get_tz_template(request):
    try:
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
    
    except Exception as err:
        method = request.method
        write_access_view_err_log(err, method, 'get_tz_template')

        return Response({'status': 'err', 'description': err}, status=status.HTTP_400_BAD_REQUEST)
    
@sync_to_async
@api_view(['GET'])
def get_presentation(request):
    try:
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
    
    except Exception as err:
        method = request.method
        write_access_view_err_log(err, method, 'get_presentation')

        return Response({'status': 'err', 'description': err}, status=status.HTTP_400_BAD_REQUEST)

@sync_to_async 
@permission_classes([IsAuthenticated,]) 
@api_view(['GET'])
def download_admin_file(request):
    try:
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
    
    except Exception as err:
        method = request.method
        write_access_view_err_log(err, method, 'download_admin_file')

        return Response({'status': 'err', 'description': err}, status=status.HTTP_400_BAD_REQUEST)
    
def robots_txt_file(request):
    robots_txt_file_path = f'{settings.SEO_FOLDER}/robots.txt'
    if os.path.exists(robots_txt_file_path):
        return FileResponse(open(f'{robots_txt_file_path}', 'rb'), content_type='text/plain')
    return render(request, '404.html', status=404)

def sitemap_xml_file(request):
    sitemap_xml_file_path = f'{settings.SEO_FOLDER}/sitemap.xml'
    if os.path.exists(sitemap_xml_file_path):
        return FileResponse(open(f'{sitemap_xml_file_path}', 'rb'), content_type='application/xml')
    return render(request, '404.html', status=404)

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)
