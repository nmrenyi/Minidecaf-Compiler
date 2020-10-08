
class BaseIRStr:
    '''
    base class for different IR types, with genAsm() method to generate asm commands according to the IR type
    '''
    def __repr__(self):
        return self.__str__()
    def genAsm(self):
        pass

class Const(BaseIRStr):
    '''
    push an integer onto the ir stack
    '''
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
    '''
    return an integer from the ir stack
    '''
    def __str__(self):
        return f"ret"
    def genAsm(self):
        # return value is saved in a0
        return [f"lw a0, 0(sp)", f"addi sp, sp, 4"]

class Unary(BaseIRStr):
    '''
    store unary operations
    '''
    ir_unary_ops = {'!':'lnot', '~':'not', '-':'neg'}
    asm_unary_ops = {'!':'seqz', '~':'not', '-':'neg'}
    def __init__(self, op:str):
        '''
        op is the str of '!', '~', '-'
        '''
        assert(op in self.ir_unary_ops)
        self.op = op
    def __str__(self):
        return self.ir_unary_ops[self.op]
    
    def genAsm(self):
        return [f'lw t1, 0(sp)', f'{self.asm_unary_ops[self.op]} t1, t1', 'sw t1, 0(sp)']

class Binary(BaseIRStr):
    '''
    store binary operations
    '''
    binary_ops = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '%': 'rem'}
    def __init__(self, op:str):
        '''
        op is the str of '+', '-', '*', '/', '%'
        '''
        assert(op in self.binary_ops)
        self.op = op
    
    def __str__(self):
        return self.binary_ops[self.op]
    
    def genAsm(self):
        return ['lw t1, 4(sp)', 
                'lw t2, 0(sp)',
                f'{self.binary_ops[self.op]} t1, t1, t2',
                'addi sp, sp, 4',
                'sw t1, 0(sp)'
                ]

