MIN_INT = -2 ** 31
MAX_INT = 2 ** 31 - 1

class BaseIRStr:
    def __repr__(self):
        return self.__str__()

class Const(BaseIRStr):
    def __init__(self, v:int):
        # range check
        assert MIN_INT <= v
        assert v <= MAX_INT
        self.v = v

    def __str__(self):
        return f"const {self.v}"


class Ret(BaseIRStr):
    def __str__(self):
        return f"ret"



