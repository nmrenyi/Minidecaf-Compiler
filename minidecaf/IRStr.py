
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
    binary_ops = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '%': 'rem',
                '==': 'eq', '!=': 'ne',
                '<': 'slt', '<=':'le', '>': 'sgt', '>=': 'ge',
                '&&': 'land', '||': 'lor'}
    def __init__(self, op:str):
        '''
        op should be in self.binary_ops
        '''
        assert(op in self.binary_ops)
        self.op = op
    
    def __str__(self):
        return self.binary_ops[self.op]
    def _load_t1(self):
        return 'lw t1, 4(sp)'

    def _load_t2(self):
        return 'lw t2, 0(sp)'
    
    def _store_t1(self):
        return 'sw t1, 0(sp)'
    
    def _add_stack(self):
        return 'addi sp, sp, 4'
    
    def _header(self):
        return [self._load_t1(), self._load_t2()]

    def _trailer(self):
        return [self._add_stack(), self._store_t1()]


    def genAsm(self):
        if self.op == '&&':
            result = self._header()
            result.extend(
                [
                    'snez t1, t1',
                    'snez t2, t2',
                    'and t1, t1, t2'
                ]
            )
            result.extend(self._trailer())
            return result
        
        elif self.op == '||':
            result = self._header()
            result.extend(
                [
                    'or t1, t1, t2',
                    'snez t1, t1'
                ]
            )
            result.extend(self._trailer())
            return result

        elif self.op in {'==' ,'!='}:
            eq_asm_dict = { "==": "seqz", "!=": "snez" }
            result = self._header()
            result.extend(
                [
                    f"sub t1, t1, t2", 
                    f"{eq_asm_dict[self.op]} t1, t1"
                ]
            )
            result.extend(self._trailer())
            return result

        elif self.op == '>=':
            result = Binary('<').genAsm()
            result.extend(Unary('!').genAsm())
            return result

        elif self.op == '<=':
            result = Binary('>').genAsm()
            result.extend(Unary('!').genAsm())
            return result

        # other operands, follow the general rule
        return [self._load_t1(), 
                self._load_t2(),
                f'{self.binary_ops[self.op]} t1, t1, t2',
                self._add_stack(),
                self._store_t1()
                ]

