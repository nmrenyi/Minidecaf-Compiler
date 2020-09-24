
class BaseIRStr:
    def __repr__(self):
        return self.__str__()
    def genAsm(self):
        pass

class Const(BaseIRStr):
    def __init__(self, v:int):
        # range check
        MIN_INT = -2 ** 31
        MAX_INT = 2 ** 31 - 1
        assert MIN_INT <= v
        assert v <= MAX_INT
        self.v = v

    def __str__(self):
        return f"const {self.v}"

    def genAsm(self):
        return [f"addi sp, sp, -4", f"li t1, {self.v}", f"sw t1, 0(sp)"]

class Ret(BaseIRStr):
    def __str__(self):
        return f"ret"
    def genAsm(self):
        # return value is saved in a0
        return [f"lw a0, 0(sp)", f"addi sp, sp, 4"]




