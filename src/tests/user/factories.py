from factory.django import DjangoModelFactory
from faker import Faker

from user.models import User

faker = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    is_superuser = False

