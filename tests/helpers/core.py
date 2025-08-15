from uuid import uuid4


class FakeWithID:
    def __init__(self, **kwargs):
        self.id = uuid4()
        for key, value in kwargs.items():
            setattr(self, key, value)
