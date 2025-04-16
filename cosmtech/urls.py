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
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from api.utils import create_upload_folders, rebuild_json
from api.views import index, default, favicon_view
from api.views import CallbackRequestView, RequestOrderView, RequestConsultView, \
ContactsRequestView,  QuizOrderView, QuestionOrderView, TzOrderView, CityDataView, \
    VacancyView, SupplierView, SuppliersTypeView, ForClientsRequestView, ExcursionProductionView, \
    DecorativeCosmeticView, SpecForProductionView, NewsView, CurrencyCourseView, download_admin_file, get_presentation, get_tz_template

from api.views import CallbackRequestView, RequestOrderView, RequestConsultView, ContactsRequestView, download_admin_file



create_upload_folders()
# rebuild_json()
urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    path('api/callbackreq/', CallbackRequestView.as_view()),
    path('api/order/', RequestOrderView.as_view()),
    path('api/consultreq/', RequestConsultView.as_view()),
    path('api/contactreq/', ContactsRequestView.as_view()),
    path('api/city/', CityDataView.as_view()),
    path('api/quiz/', QuizOrderView.as_view()),
    path('api/quiz/question/', QuestionOrderView.as_view()),
    path('api/quiz/tz/', TzOrderView.as_view()),
    path('api/admin_download/', download_admin_file),
    path('api/vacancy/', VacancyView.as_view()),
    path('api/suppliers/',SupplierView.as_view()),
    path('api/suppliers-type/',SuppliersTypeView.as_view()),
    path('api/clients/request/', ForClientsRequestView.as_view()),
    path('api/clients/excursion/', ExcursionProductionView.as_view()),
    path('api/decorative-cosmetic/', DecorativeCosmeticView.as_view()),
    path('api/specification/', SpecForProductionView.as_view()),
    path('api/news/', NewsView.as_view()),
    path('api/currency/', CurrencyCourseView.as_view()),
    path('company_files/presentation/', get_presentation),
    path('company_files/tz/', get_tz_template,),
    # re_path(r'^favicon\.ico$', favicon_view),
    re_path('.*', default),
]+ static(settings.UPLOAD_FILES, document_root=settings.ORDER_FILES)