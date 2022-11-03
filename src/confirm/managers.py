from django.db import models
import exceptions


class ConfirmBaseManager(models.Manager):
    def get_confirmed(self, secret_code: str, type_confirm: str):
        confirm_obj = super().get_queryset().filter(
            secret_code=secret_code,
            type_confirm=type_confirm
        )

        if not confirm_obj.exists():
            raise exceptions.ConfirmObjNotFound

        confirm_obj = confirm_obj.get()

        if not confirm_obj.confirmed:
            raise exceptions.ConfirmObjNotConfirmed

        return confirm_obj


class ConfirmEmailManager(ConfirmBaseManager):
    pass


class ConfirmPhoneManager(ConfirmBaseManager):
    pass
