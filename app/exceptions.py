from . import flavors


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class UnknownFlavor(Exception):

    def __init__(self, *args, **kwargs):
        message = (
            'Allowed flavors are ' +
            ', '.join([f"'{flavor}'" for flavor in flavors.allowed_flavors()]) +
            '.'
        )
        super().__init__(message, *args, **kwargs)


class FlavorNotSet(InvalidUsage):

    def __init__(self, *args, **kwargs):
        super().__init__(message='No flavor has been set.', *args, **kwargs)
