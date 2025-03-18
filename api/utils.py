import os
import json
import re
import uuid
import base64
import random
from datetime import datetime
from pprint import pprint
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Q
from asgiref.sync import sync_to_async

from .models import Order, Client

from docxtpl import DocxTemplate

def create_upload_folders():
    upload_files = f'{os.getcwd()}/upload_files/'
    order_files = f'{upload_files}/order_files/'
    cooperation_files = f'{upload_files}/cooperation_files/'
    download_files = f'{os.getcwd()}/download/'
    company_files = f'{download_files}/company_files/'
    quiz_files = f'{upload_files}/quiz_files/'
    resume_files = f'{upload_files}/resume_files/'
    log_folder = f'{os.getcwd()}/logs/'

    if not os.path.exists(f'{upload_files}'):
        os.mkdir(f'{upload_files}')
    if not os.path.exists(f'{order_files}'):
        os.mkdir(f'{order_files}')
    if not os.path.exists(f'{cooperation_files}'):
        os.mkdir(f'{cooperation_files}')
    if not os.path.exists(f'{download_files}'):
        os.mkdir(f'{download_files}')
    if not os.path.exists(f'{company_files}'):
        os.mkdir(f'{company_files}')
    if not os.path.exists(f'{quiz_files}'):
        os.mkdir(f'{quiz_files}')
    if not os.path.exists(f'{resume_files}'):
        os.mkdir(f'{resume_files}')
    if not os.path.exists(f'{log_folder}'):
        os.mkdir(log_folder)

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


async def select_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_templates/email_templates.json'

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
    
    with open(log_file_path, 'a+') as file:
        file.write(f'{err_description} \n')

async def write_access_view_err_log(err, method, view_name=''):
    current_date = datetime.now().replace(microsecond=0)
    err_description = f'view_func: {view_name} ({method}) date: {current_date} err_descr: {err}'
    log_file_path = f'{os.getcwd()}/logs/access_views_err.txt'

    with open(log_file_path, 'a+') as file:
        file.write(f'{err_description} \n')
    
    
    
def send_email_to_client(email_data, client_email):
    pass

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

def validate_email(email_str):
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

def create_specification_file(data):
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
    
    document_file = DocxTemplate(specification_template_path)

    order_time = get_time(datetime.now())
    specification_data = keys_form_camel_case_to_python_style(data)
    specification_data['order_number'] = specification_order
    specification_data['order_date'] = order_time

    if specification_data.get('services') and len(specification_data['services']) > 0:
        specification_data['services'] = ''.join(f'{i}, 'for i in specification_data['services'])

    document_file.render(specification_data)
    document_file.save(specification_tmp_file_path)

    specification_info['order_number'] = specification_data['order_number']
    specification_info['tmp_file_path'] = specification_tmp_file_path
    specification_info['order_date'] = specification_data['order_date']

    return specification_info

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
        'decor': 'Декоративная косметика производство',
        'msg': 'Мессанджеры',
        'phone': 'Телефон',
        'email': 'Email',

    }
    return request_types.get(value)

def generate_simple_order_number(prefix):
    order_modifer = []
    for i in range(6):
        order_modifer.append(chr(random.randint(ord('A'), ord('Z'))))
    order_modifer.append(prefix)
    order_modifer = f''.join(map(str, order_modifer))

    return order_modifer

def generate_quiz_order_number():
    order_modifer = []
    for i in range(6):
        order_modifer.append(chr(random.randint(ord('A'), ord('Z'))))
    order_modifer.append('_qz_oer')
    order_modifer = f''.join(map(str, order_modifer))

    return order_modifer


async def find_existing_client(phone='', email=''):
    if phone and email:
        async for client in Client.objects.filter(Q(email=email) | Q(phone=phone)):
            target_client = client

    return target_client

async def find_existing_data_by_contact(model, phone='', email=''):
    if phone and email:
        async for data in model.objects.filter(Q(email=email) | Q(phone=phone)):
            target_data = data
            
    return target_data

async def get_all_city_data(model):
    all_city = []
    async for city in model.objects.all().values():
        all_city.append(city)

    return all_city

async def generate_order_number(order_type, client_id=1):
    not_format_date = datetime.now()
    time = get_time(not_format_date)
    order_type_arr = [
        {'name': 'contract', 'length': 6, 'prefix': 'cprod'},
        {'name': 'contract_decorative', 'length': 3, 'prefix': 'cprod_dec'},
        {'name': 'cooperation', 'length': 4, 'prefix': 'coop'},
        {'name': 'quiz', 'length': 4, 'prefix': 'quiz'},
        {'name': 'quiz_consult', 'length': 4, 'prefix': 'qzcut'},
        {'name': 'tz_cosm', 'length': 4, 'prefix': 'tz_cprod'},
        {'name': 'tz_decor', 'length': 4, 'prefix': 'tz_dprod'},
    ]
    target_order_type = list(filter(lambda x: x.get('name') == order_type, order_type_arr))
    order_modifer = list()

    for i in range(target_order_type[0].get('length')):
        order_modifer.append(chr(random.randint(ord('A'), ord('Z'))))
    order_modifer = f"{target_order_type[0].get('prefix')}_" + ''.join(map(str, order_modifer)) + f'_{client_id}'

    return {'order_number': order_modifer, 'not_format_date': not_format_date, 'order_date': time}