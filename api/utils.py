import os
import json


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

def select_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_templates/email_tepmlates.json'
    with open(json_path, 'r') as json_file:
        template_data = json.load(json_file)
    
    target_template = list(filter(lambda item: item.get('template_name') == order_type, template_data))
    if len(target_template) > 0:
        return target_template[0]
    return target_template

