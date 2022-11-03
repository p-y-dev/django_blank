from django.urls import path, include

from confirm import views

app_name = 'confirm'

urlpatterns = [
    path('', views.confirm, name='confirm'),
    path('email/', include([
        path('create/', views.create_confirm_email, name='create_confirm_email'),
    ])),
    path('phone/', include([
        path('create/', views.create_confirm_phone, name='create_confirm_phone'),
    ])),
]
