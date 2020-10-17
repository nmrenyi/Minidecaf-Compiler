from minidecaf.utils import push_int
from minidecaf.utils import push_reg
from minidecaf.utils import pop
# import minidecaf.AsmGenerator

class BaseIRStr:
    '''
    base class for different IR types, with genAsm() method to generate asm commands according to the IR type
    '''
    def __repr__(self):
        return self.__str__()
    def genAsm(self):
        pass

class Call(BaseIRStr):
    '''
    parameters are pushed onto stack from right to left before call instruction
    '''
    def __init__(self, func:str, para_cnt):
        self.func = func
        self.para_cnt = para_cnt

    def __str__(self):
        return f"call {self.func}"

    def genAsm(self):
        return [f'call {self.func}'] + pop(None) * self.para_cnt + push_reg('a0')

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
        return [f"beqz x0, main_exit"]
        # return [f"lw a0, 0(sp)", f"addi sp, sp, 4"]

class Load(BaseIRStr):
    '''
    load stack top address data to stack top
    '''
    def __str__(self):
        return 'load'
    
    def genAsm(self):
        '''
        stack top as the address (popped to t1)
        go to the address and access result 
        store the result in t1 and push to the stack
        '''
        return (pop('t1') + ['lw t1, 0(t1)'] + push_reg('t1'))

class Pop(BaseIRStr):
    '''
    pop from the stack (add stack pointer) without reg changes
    '''
    def __str__(self):
        return 'pop'
    def genAsm(self):
        '''
        just pop (add stack pointer)
        no registers are changed here
        '''
        return pop(None)


class Store(BaseIRStr):
    '''
    store stackTop + 4 data to 0(stackTop) address
    '''
    def __str__(self):
        return 'store'
    def genAsm(self):
        '''
        t1(stack top + 4) is the data to be stored
        t2(stack top) is the address where the data should be stored
        this operations performs storing t1 in 0(t2)
        '''
        return pop('t2') + pop('t1') + ["sw t1, 0(t2)"] + push_reg('t1')
        
class FrameSlot(BaseIRStr):
    '''
    save the var's address to the stack top    
    '''
    def __init__(self, fpOffset:int):
        assert fpOffset < 0
        self.offset = fpOffset

    def __str__(self):
        return f'frameslot {self.offset}'
    
    def genAsm(self):
        '''
        save offset(fp) to stack
        '''
        return push_reg('fp') + push_int(self.offset) + Binary('+').genAsm()

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

class Branch(BaseIRStr):
    '''
    Branch operations
    '''
    branchOps = ["br", "beqz", "bnez", "beq"]
    def __init__(self, op, label:str):
        assert(op in self.branchOps)
        self.op = op
        self.label = label

    def __str__(self):
        return f"{self.op} {self.label}"
    
    def genAsm(self):
        if self.op == 'br':
            return [f'j {self.label}']
        if self.op == 'beqz':
            return pop('t1') + [f'beqz t1, {self.label}']
        if self.op == 'bnez':
            return pop('t1') + [f'bnez t1, {self.label}']
        
class Label(BaseIRStr):
    '''
    label for branch
    '''
    def __init__(self, label:str):
        self.label = label

    def __str__(self):
        return f"{self.label}:"

    def genAsm(self):
        return [f"{self.label}:"]

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

