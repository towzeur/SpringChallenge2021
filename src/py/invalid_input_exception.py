

class InvalidInputException(Exception):

    def __init__(self, expected: str, got: str):
        self._expected: str = expected
        self._got: str = got
        super().__init__(f"Invalid Input: Expected {expected} but got '{got}'")


    def getExpected(self) -> str: 
        return self._expected
    

    def getGot(self) -> str:
        return self._got
