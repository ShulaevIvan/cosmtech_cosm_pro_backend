"""
URL configuration for cosmtech project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path
from api.views import CallbackRequestView, RequestOrderView, RequestConsultView, ContactsRequestView

upload_files = f'{os.getcwd()}/upload_files/'
order_files = f'{upload_files}/order_files/'
cooperation_files = f'{upload_files}/cooperation_files/'

if not os.path.exists(f'{upload_files}'):
    os.mkdir(f'{upload_files}')

if not os.path.exists(f'{order_files}'):
    os.mkdir(f'{order_files}')

if not os.path.exists(f'{cooperation_files}'):
    os.mkdir(f'{cooperation_files}')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/callbackreq/', CallbackRequestView.as_view()),
    path('api/order/', RequestOrderView.as_view()),
    path('api/consultreq/', RequestConsultView.as_view()),
    path('api/contactreq/', ContactsRequestView.as_view())
]
