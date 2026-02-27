from uuid import UUID, uuid4

from highload_payments.domain.ports.id_generator import IdGenerator


class UUID4Generator(IdGenerator):
    def new(self) -> UUID:
        return uuid4()

