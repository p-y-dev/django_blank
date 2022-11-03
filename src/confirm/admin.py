from django.contrib import admin

from confirm.models import ConfirmEmail, ConfirmPhone

admin.site.register([ConfirmEmail, ConfirmPhone])
