import os
import json
import re
import uuid
import base64
import random
import requests
import xml.etree.ElementTree as XMLET
from lxml import etree
import aiofiles
import asyncio
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Q
from asgiref.sync import sync_to_async

from .models import Client

from docxtpl import DocxTemplate


async def select_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_templates/email_templates.json'

    with open(json_path, 'r') as json_file:
        template_data = json.load(json_file)
    
    target_template = list(filter(lambda item: item.get('template_name') == order_type, template_data))
    if len(target_template) > 0:
        return target_template[0]
    
    return target_template

async def select_client_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_templates/client_email_templates.json'

    with open(json_path, 'r') as json_file:
        template_data = json.load(json_file)
    
    target_template = list(filter(lambda item: item.get('template_name') == order_type, template_data))
    if len(target_template) > 0:
        return target_template[0]
    
    return target_template

async def send_order_to_main_email(email_template, email_data, time='', order_number=''):
    try:
        has_multiple_files = email_data.get('files')
        has_file = email_data.get('file')
        msg_mail = EmailMessage(
            f"{email_template.get('email_subject')}", 
            f"""
                <h4>Описание:</h4>
                <p>{email_template.get('email_body_description')}</p>

                <h4>Данные:</h4>
                <ul>
                    {''.join(f"<li>{item.get('value')} : {email_data.get(item.get('name'))}</li>" for item in email_template.get('fields'))}
                </ul>

                <p>№ запроса: <strong>{order_number}</strong></p>
                <p><strong>{time}</strong></p>

            """,
            f'{settings.EMAIL_HOST_USER}', [f"{settings.EMAIL_ORDER_ADDRESS}"]
        )
        msg_mail.content_subtype = "html"
        if has_multiple_files:
            for file_path in email_data.get('files'):
                msg_mail.attach_file(f'{file_path}')
        elif has_file:
            msg_mail.attach_file(f"{email_data.get('file')}")
        msg_mail.send()
        
    except Exception as err:
        await write_email_err_log(err, email_template.get('template_name'))


async def write_email_err_log(err, template, order_num=''):
    current_date = datetime.now().replace(microsecond=0)
    err_description = f'order_num: {order_num} date: {current_date} send_form: {template}  err_descr: {err}'
    log_file_path = f'{os.getcwd()}/logs/mail_err.txt'
    
    async with aiofiles.open(log_file_path, 'a+') as file:
        await file.write(f'{err_description} \n')

async def write_access_view_err_log(err, method, view_name=''):
    current_date = datetime.now().replace(microsecond=0)
    err_description = f'view_func: {view_name} ({method}) date: {current_date} err_descr: {err}'
    log_file_path = f'{os.getcwd()}/logs/access_views_err.txt'

    async with aiofiles.open(log_file_path, 'a+') as file:
        await file.write(f'{err_description} \n')
    
async def send_email_to_client(email_template, client_name, client_email, order):
    try:
        if not client_name:
            client_name = 'Аноним'
        order_number = order.get('order_number')
        order_time = order.get('order_date')

        pre_description = f'Ваш номер заявки {order_number}.'
        email_template['email_subject'] = email_template.get('email_subject')
        organization_contacts = email_template.get('organization_contacts')

        msg_mail = EmailMessage(
            f"{email_template.get('email_subject')}", 
            f"""
                <h4>Описание:</h4>
                <p>Здравствуйте {client_name}!</p>
                <p>{email_template.get('email_body_description')}</p>


                <p>№ запроса: <strong>{order_number}</strong></p>
                <p><strong>{order_time}</strong></p>

                <h4>Контакты ООО Космотех</h4>
                <ul>
                    {''.join(f"<li>{item.get('name')} : <a href='{item.get('link')}'>{''.join(item['value'])}</a></li>" for item in organization_contacts)}
                </ul>

            """,
            f'{settings.EMAIL_HOST_USER}', [f"{client_email}"]
        )
        msg_mail.content_subtype = "html"
        msg_mail.send()

    except Exception as err:
        await write_email_err_log(err, email_template.get('template_name'), order_number)


async def create_specification_file(data):
    specification_info = dict()
    specification_data = dict()
    specifications_folder = f'{os.getcwd()}/download/company_files/specifications'

    if not os.path.exists(specifications_folder):
        os.mkdir(specifications_folder)

    specification_filename = f'spec_{uuid.uuid4()}'
    specification_order = generate_specification_number(specification_filename)
    specification_format = '.docx'
    specification_template_path = f'{os.getcwd()}/download/company_files/specification_template.docx'
    specification_tmp_file_path = f'{specifications_folder}/{specification_filename}{specification_format}'

    order_time = get_time(datetime.now())
    specification_data = keys_form_camel_case_to_python_style(data)
    specification_data['order_number'] = specification_order
    specification_data['order_date'] = order_time

    if specification_data.get('services') and len(specification_data['services']) > 0:
        specification_data['services'] = ''.join(f'{i}, 'for i in specification_data['services'])
    
    await create_word_template(specification_template_path, specification_data, specification_tmp_file_path)

    specification_info['order_number'] = specification_data['order_number']
    specification_info['tmp_file_path'] = specification_tmp_file_path
    specification_info['order_date'] = specification_data['order_date']

    return specification_info

async def create_word_template(template_path, data_to_template, file_path):

    document_file = DocxTemplate(template_path)
    document_file.render(data_to_template)
    document_file.save(file_path)

    return document_file

async def create_file(file_obj, path):
    ext = re.findall(r'.\w+$', file_obj['name'])[0]
    full_name = f"{path}{uuid.uuid4()}{ext}"

    async with aiofiles.open(full_name, "wb") as file:
        await file.write(base64.b64decode(file_obj['file']))

    return full_name

async def file_to_base64(path):
    file_path = f'{os.getcwd()}/{path}'
    file_format = re.search(r'\.\w+$', file_path)
    file_data = dict()
    
    text_mime_types = [
        {'ext': 'txt', 'type': 'text/plain'}, 
        {'ext': 'css', 'type': 'text/css'}, 
        {'ext': 'js', 'type': 'text/javascript'}, 
        {'ext': 'xml', 'type': 'application/xml'},
        {'ext': 'pdf', 'type': 'application/pdf'}
    ]
    image_mime_types = [
        {'ext': 'jpg', 'type': 'image/jpeg'}, 
        {'ext': 'jpeg', 'type': 'image/jpeg'}, 
        {'ext': 'png', 'type': 'image/png'}, 
        {'ext': 'gif', 'type': 'image/gif'},
        {'ext': 'svg', 'type': 'image/svg+xml'}
    ]
    media_mime_types = [
        {'ext': 'mp3', 'type': 'audio/mpeg'},
        {'ext': 'mp4', 'type': 'video/mp4'}, 
    ]

    if file_format and file_format[0]:
        file_data['ext'] = file_format[0].replace('.', '')
        check_is_media = list(filter(lambda x: x['ext'] == file_data['ext'], media_mime_types))
        check_is_image = list(filter(lambda x: x['ext'] == file_data['ext'], image_mime_types))
        check_is_doc = list(filter(lambda x: x['ext'] == file_data['ext'], text_mime_types))

        if not os.path.exists(file_path) and not check_is_media and not check_is_doc:
            file_path = f'{os.getcwd()}/upload_files/news_files/default.jpg'

        async with aiofiles.open(file_path, 'rb') as file:
            file_str = await file.read()
            file_data['file'] = base64.b64encode(file_str).decode('ascii')
            if check_is_media and len(check_is_media) > 0:
                file_data['mime'] = check_is_media[0].get('type')
            elif check_is_image and len(check_is_image) > 0:
                file_data['mime'] = check_is_image[0].get('type')
            elif check_is_doc and len(check_is_doc) > 0:
                file_data['mime'] = check_is_doc[0].get('type')
            return file_data
    return ''

async def get_paragraphs_from_text(text):
    text_length = len(text)
    result_par = []
    start_index = 0
    if text_length > 100:
        find_all_par_indexes = [i.start() for i in re.finditer('\|', text)]

        for p_index in find_all_par_indexes:
           result_par.append(text[start_index : p_index])
           start_index = p_index + 1
        result_par = [p.replace(' ', '') if p.startswith((' ', '\t')) else p for p in result_par]

        return result_par
    
    return result_par.append(text.replace(r'^\s', ''))

async def get_currency_daily_course(date, prev_date):
    try:
        event_loop = asyncio.get_event_loop()
        currency_api_url = 'https://cbr.ru/scripts/XML_daily.asp'
        currency_folder = f'{os.getcwd()}/upload_files/news_files/currency'
        xml_path = f'{currency_folder}/{date}.xml'
        prev_xml_file = f'{currency_folder}/{prev_date}.xml'
        json_path = f'{currency_folder}/currency.json'
        json_data = list()

        if not os.path.exists(xml_path):
            if os.path.exists(prev_xml_file):
                for item in os.scandir(currency_folder):
                    if item.is_file():
                        os.remove(item)

            response = await event_loop.run_in_executor(None, requests.get, currency_api_url)

            async with aiofiles.open(f'{xml_path}', 'w+') as file:
                await file.write(response.text)
                

        parser = etree.XMLParser(recover=True,encoding='utf-8')
        xml_file = XMLET.parse(xml_path,parser=parser)

        for currency_item in xml_file.findall('Valute'):
            json_obj = {
                'name': currency_item.find('Name').text,
                'char_code': currency_item.find('CharCode').text,
                'value': currency_item.find('Value').text,
            }
            json_data.append(json_obj)

        result_json = json.dumps(json_data)

        async with aiofiles.open(f'{json_path}', 'w+') as file:
            await file.write(result_json)

    except Exception as err:
        async with aiofiles.open(f'{os.getcwd()}/logs/currency_err.txt', 'a+') as file:
            await file.write(err + '\n')

async def read_json_file_by_parh(path):
    async with aiofiles.open(path , 'r') as file:
        file_data = await file.read()
    
    return json.loads(file_data)


async def find_existing_client(phone='', email=''):
    if phone or email:
        async for client in Client.objects.filter(Q(email=email) | Q(phone=phone)):
            target_client = client

    return target_client

async def find_existing_data_by_contact(model, phone='', email=''):
    if phone or email:
        async for data in model.objects.filter(Q(email=email) | Q(phone=phone)):
            target_data = data
            
    return target_data

async def get_all_data_from_model(model):
    model_data = []
    async for data in model.objects.all().values():
        model_data.append(data)

    return model_data

async def generate_order_number(order_type, client_id=1):
    not_format_date = datetime.now()
    time = get_time(not_format_date)
    order_type_arr = [
        {'name': 'consult', 'length': 4, 'prefix': 'ct_rq'},
        {'name': 'contract', 'length': 6, 'prefix': 'cprod'},
        {'name': 'contract_decorative', 'length': 3, 'prefix': 'cprod_dec'},
        {'name': 'cooperation', 'length': 4, 'prefix': 'coop'},
        {'name': 'quiz', 'length': 4, 'prefix': 'quiz'},
        {'name': 'quiz_consult', 'length': 4, 'prefix': 'qzcut'},
        {'name': 'quiz_tz', 'length': 4, 'prefix': 'qztz'},
        {'name': 'vacancy_req', 'length': 4, 'prefix': 'vyrq'},
        {'name': 'supl_consult', 'length': 4, 'prefix': 'sup_ct'},
        {'name': 'excursion_req', 'length': 4, 'prefix': 'ex_rq'},
        {'name': 'tz_cosm', 'length': 4, 'prefix': 'tz_cprod'},
        {'name': 'tz_decor', 'length': 4, 'prefix': 'tz_dprod'},
    ]
    target_order_type = list(filter(lambda x: x.get('name') == order_type, order_type_arr))
    order_modifer = list()

    for i in range(target_order_type[0].get('length')):
        order_modifer.append(chr(random.randint(ord('A'), ord('Z'))))
    order_modifer = f"{target_order_type[0].get('prefix')}_" + ''.join(map(str, order_modifer)) + f'_{client_id}'

    return {'order_number': order_modifer, 'not_format_date': not_format_date, 'order_date': time}


def create_upload_folders():
    upload_files = f'{os.getcwd()}/upload_files/'
    order_files = f'{upload_files}/order_files/'
    cooperation_files = f'{upload_files}/cooperation_files/'
    download_files = f'{os.getcwd()}/download/'
    company_files = f'{download_files}/company_files/'
    quiz_files = f'{upload_files}/quiz_files/'
    resume_files = f'{upload_files}/resume_files/'
    log_folder = f'{os.getcwd()}/logs/'
    email_templates = f'{os.getcwd()}/email_templates'
    news_folder = f'{os.getcwd()}/upload_files/news_files/'
    news_banners = f'{os.getcwd()}/upload_files/news_files/banners/'
    news_videos = f'{os.getcwd()}/upload_files/news_files/videos/'
    currency_folder = f'{os.getcwd()}/upload_files/news_files/currency/'
    seo_folder = f'{os.getcwd()}/seo_files/'
    
    path_arr = [
        upload_files,order_files,cooperation_files,
        download_files, company_files, resume_files,
        log_folder, quiz_files, email_templates,
        news_folder, news_banners, news_videos, currency_folder,
        seo_folder
    ]
    for path in path_arr:
        if not os.path.exists(path):
            os.mkdir(path)

def rebuild_json():
    result_data = []
    i = 0
    with open (f'{os.getcwd()}/download/fixtures_city.json', 'r') as file:
        data = json.load(file)
        for obj in data:
            i = i + 1
            result_data.append({
                "pk": i,
                "model": "api.CityData",
                "fields": {
                    "name": f'{obj["name"]}',
                    "subject": f'{obj["subject"]}',
                    "population": int(f'{obj["population"]}'),
                    "range": int(obj["range"]),
                    "lat": float(obj["coords"]["lat"]),
                    "lon": float(obj["coords"]["lon"])
                }
            })
        with open(f'{os.getcwd()}/download/fixtures_city2.json', 'w') as file:
            json.dump(result_data, file, ensure_ascii=False, indent=4)

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


def get_request_name(value):
    request_types = {
        'contract': 'Контрактное производство',
        'lab': 'Услуги лаборатории',
        'pack': 'Упаковка и сопровождение',
        'cert': 'Сертификаиця продукции',
        'trade': 'Торговое предложение',
        'cooperation': 'Сотрудничество',
        'decor': 'Декоративная косметика производство',
        'msg': 'Мессанджеры',
        'phone': 'Телефон',
        'email': 'Email',

    }
    return request_types.get(value)

def validate_email(email_str):
    if not email_str:
        return False
    email_pattern = r'\S*\@\S*\.\w{2,10}$'
    check_email_valid = re.match(email_pattern, email_str)
    if check_email_valid and len(check_email_valid.group(0)) > 0:
        return True
    return False

def generate_specification_number(filename):
    pattern = r'^spec_[a-z|0-9|A-Z]{8}'
    check_str = re.match(pattern, filename)
    if check_str and check_str.group(0):
        return check_str.group(0)
    return False

def keys_form_camel_case_to_python_style(data):
    result_dict = dict()

    for key, value in data.items():
        valid_key = ''.join('_' + char.lower() if char.isupper() else char.strip() for char in key).strip()
        result_dict[valid_key] = value

    return result_dict
