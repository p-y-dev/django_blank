from django.urls import path, include

from user.views import (
    registration, login, password, email_or_phone
)

app_name = 'user'

urlpatterns = [
    path('registration/', registration.registration, name='registration'),
    path('login/', include([
        path('email/', login.login_by_email, name='login_by_email'),
        path('phone/', login.login_by_phone, name='login_by_phone'),
    ])),
    path('password/', include([
        path('', password.change, name='change_password'),
        path('confirm/', password.change_by_confirm, name='change_password_by_confirm'),
    ])),
    path('email_or_phone/', email_or_phone.change, name='change_email_or_phone'),
]
