import uuid

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from confirm.choices import TypeConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from confirm.utils import generate_confirm_code
from tests.utils import rand_mobile_phone

faker = Faker()


class BaseConfirmFactory(DjangoModelFactory):
    secret_code = factory.LazyAttribute(lambda _: uuid.uuid4())
    confirm_code = factory.LazyAttribute(lambda _: generate_confirm_code())
    confirmed = False
    type_confirm = TypeConfirm.REGISTRATION
    created_at = factory.LazyAttribute(lambda _: timezone.now())


class ConfirmEmailFactory(BaseConfirmFactory):
    class Meta:
        model = ConfirmEmail

    email = factory.LazyAttribute(lambda _: faker.email())


class ConfirmPhoneFactory(BaseConfirmFactory):
    class Meta:
        model = ConfirmPhone

    phone = factory.LazyAttribute(lambda _: rand_mobile_phone()['phone'])
