class DisconnectError(ConnectionError):
    def __init__(self, *args):
        ConnectionError.__init__(self, *args)
