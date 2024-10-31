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
from .settings import create_upload_folders, rebuild_json
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from api.views import index, default, favicon_view
from api.views import CallbackRequestView, RequestOrderView, RequestConsultView, \
ContactsRequestView,  QuizOrderView, CityDataView, download_admin_file, get_presentation




create_upload_folders()
rebuild_json()
urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    path('api/callbackreq/', CallbackRequestView.as_view()),
    path('api/order/', RequestOrderView.as_view()),
    path('api/consultreq/', RequestConsultView.as_view()),
    path('api/contactreq/', ContactsRequestView.as_view()),
    path('api/city/', CityDataView.as_view()),
    path('api/quiz/', QuizOrderView.as_view()),
    path('api/admin_download/', download_admin_file),
    path('company_files/presentation/', get_presentation),
    re_path(r'^favicon\.ico$', favicon_view),
    re_path('.*', default),
]+ static(settings.UPLOAD_FILES, document_root=settings.ORDER_FILES)