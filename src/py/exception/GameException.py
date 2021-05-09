class GameException(Exception):
    """Base class for game exceptions in this module."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
