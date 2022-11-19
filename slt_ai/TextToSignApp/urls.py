from django.urls import path
from . import views

urlpatterns = [
    path('translate'  , views.text_to_text_translate,   name='translate'  ),
    path('restructure', views.restructure,              name='restructure'),
    path('substitute' , views.substitute ,              name='substitute' ),
    path('create'     , views.create     ,              name='create'     ),
    path(''           , views.text_to_sign ,            name='textToSign' )
]