from django.urls import path
from . import views

urlpatterns = [
    path('translatePSL', views.translate_PSL,    name='translatePSL'  ),
    path(''            , views.sign_to_text ,    name='signToText' ),
]