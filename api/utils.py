import os
import json
import re
from datetime import datetime
from pprint import pprint
from django.core.mail import EmailMessage
from django.conf import settings

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


def select_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_templates/email_templates.json'

    with open(json_path, 'r') as json_file:
        template_data = json.load(json_file)
    
    target_template = list(filter(lambda item: item.get('template_name') == order_type, template_data))
    if len(target_template) > 0:
        return target_template[0]
    
    return target_template


def send_order_to_main_email(email_template, email_data, time='', order_number=''):
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
        write_email_err_log(err, email_template.get('template_name'))


def write_email_err_log(err, template, order_num=''):
    current_date = datetime.now().replace(microsecond=0)
    err_description = f'order_num: {order_num} date: {current_date} send_form: {template}  err_descr: {err}'
    log_file_path = f'{os.getcwd()}/logs/mail_err.txt'
    
    with open(log_file_path, 'a+') as file:
        file.write(f'{err_description} \n')

def write_access_view_err_log(err, view_name=''):
    current_date = datetime.now().replace(microsecond=0)
    err_description = f'view_func: {view_name} date: {current_date} err_descr: {err}'
    log_file_path = f'{os.getcwd()}/logs/access_views_err.txt'

    with open(log_file_path, 'a+') as file:
        file.write(f'{err_description} \n')
    
    

def send_email_to_client(email_data, client_email):
    pass

def validate_email(email_str):
    email_pattern = r'\S*\@\S*\.\w{2,10}$'
    check_email_valid = re.match(email_pattern, email_str)
    if check_email_valid and len(check_email_valid.group(0)) > 0:
        return True
    return False

