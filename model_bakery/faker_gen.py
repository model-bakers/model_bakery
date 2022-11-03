from typing import Callable, Dict

from faker import Faker

FAKER = Faker()

faker_generator_mapping: Dict[str, Callable] = {
    "username": FAKER.user_name,
    "email": FAKER.email,
    "first_name": FAKER.first_name,
    "last_name": FAKER.last_name,
    "name": FAKER.name,
    "fullname": FAKER.name,
    "full_name": FAKER.name,
    "ip": FAKER.ipv4,
    "ipv4": FAKER.ipv4,
    "ipv6": FAKER.ipv6,
}
