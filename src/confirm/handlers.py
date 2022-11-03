from uuid import UUID

from django.conf import settings

import exceptions
from confirm import utils
from confirm.choices import TypeConfirm, ObjConfirm, PhoneRegion
from confirm.models import ConfirmEmail, ConfirmPhone


def create_confirm_email(email: str, type_confirm: TypeConfirm) -> ConfirmEmail:
    """
    Создание/Обновление объекта подтверждения email

    :param email: Email
    :param type_confirm: Тип подтверждения email

    :return: Созданный или обновленный объект подтверждения email
    """

    email = email.lower()

    user_filter_data = {'email': email}
    utils.type_confirm_is_available_for_user(type_confirm, user_filter_data)

    confirm_data = utils.generate_confirm_data(type_confirm)
    if settings.EMAIL_TEST_CONFIRM_CODE:
        confirm_data['confirm_code'] = '111111'

    confirmation_email = ConfirmEmail.objects.update_or_create(
        email=email,
        defaults=confirm_data
    )[0]

    return confirmation_email


def create_confirm_phone(phone: str, region: PhoneRegion, type_confirm: TypeConfirm) -> ConfirmPhone:
    """
    Создание/Обновления объекта подтверждения телефона

    :param phone: Номер телефона без кода страны
    :param region: Регион номера телефона ISO 3166-1 Alpha-2
    :param type_confirm: Тип подтверждения телефона

    :return: Созданный или обновленный объект подтверждения телефона
    """

    phone = utils.normalization_phone_number(phone, region)

    user_filter_data = {'phone': phone}
    utils.type_confirm_is_available_for_user(type_confirm, user_filter_data)

    confirm_data = utils.generate_confirm_data(type_confirm)
    if settings.PHONEL_TEST_CONFIRM_CODE:
        confirm_data['confirm_code'] = '111111'

    confirmation_phone, is_created = ConfirmPhone.objects.get_or_create(
        phone=phone,
        defaults=confirm_data
    )

    if is_created:
        return confirmation_phone

    count_sec_wait_renewal_sending = confirmation_phone.count_sec_wait_renewal_sending

    if count_sec_wait_renewal_sending == 0:
        confirm_data['count_send'] = 1
        ConfirmPhone.objects.filter(id=confirmation_phone.id).update(**confirm_data)
        return ConfirmPhone.objects.get(id=confirmation_phone.id)

    if confirmation_phone.count_send >= settings.PHONE_CONFIRM_CODE_COUNT_SEND:
        raise exceptions.ConfirmPhoneExcMaxCountSend(count_sec_wait_renewal_sending)

    sec_resend = confirmation_phone.sec_resend
    if sec_resend != 0:
        raise exceptions.ConfirmPhoneWaitBeforeSending(sec_resend)

    confirm_data['count_send'] = confirmation_phone.count_send + 1
    ConfirmPhone.objects.filter(id=confirmation_phone.id).update(**confirm_data)
    return ConfirmPhone.objects.get(id=confirmation_phone.id)


def confirm_obj(secret_code: UUID, confirm_code: str, object_confirmation: ObjConfirm):
    """
    Подтверждение объекта подтверждения номера телефона или email

    :param secret_code: Секретный код объекта подтверждения
    :param confirm_code: Код подтверждения объекта подтверждения
    :param object_confirmation: Тип объекта подтверждения
    """

    confirm_model = ConfirmEmail if object_confirmation == ObjConfirm.EMAIL else ConfirmPhone

    confirmation_obj = confirm_model.objects.filter(
        secret_code=secret_code, confirm_code=confirm_code, confirmed=False
    )
    if not confirmation_obj.exists():
        raise exceptions.ConfirmObjNotFound

    confirmation_obj = confirmation_obj.get()

    if confirmation_obj.is_expired:
        raise exceptions.ConfirmCodeExpired

    confirmation_obj.confirmed = True
    confirmation_obj.save()
