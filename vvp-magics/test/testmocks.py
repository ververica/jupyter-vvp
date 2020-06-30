class ArgsMock:
    def __init__(self, parameters):
        self.parameters = parameters


class ShellMock:
    def __init__(self, user_ns):
        self.user_ns = user_ns
