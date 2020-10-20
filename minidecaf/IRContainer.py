import minidecaf.IRStr
from minidecaf.NameParser import ParamInfo
from minidecaf.IRStr import BaseIRStr


class IRContainer:
    """
    A List Containing IR string, with add method
    __str__ method returns the string representation of IR
    """

    def __init__(self):
        self.current_instructions = []
        self.curName = None
        self.curParamInfo = None
        self.funcs = []
        self.globs = []
        self.funcDecl = []

    def __str__(self):
        return "main:\n\t" + '\n\t'.join(map(str, self.current_instructions))

    def add(self, ir: minidecaf.IRStr.BaseIRStr):
        self.current_instructions.append(ir)

    def add_func_decl(self, decl: str):
        self.funcDecl.append(decl)

    def add_list(self, ir_list):
        self.current_instructions.extend(ir_list)

    def add_global(self, global_info):
        assert global_info.var.offset is None
        self.globs.append(global_info)

    def enter_function(self, name: str, param_info):
        self.curName = name
        self.curParamInfo = param_info
        self.current_instructions = []

    def exit_function(self):
        self.funcs.append(IRFunc(self.curName, self.curParamInfo, self.current_instructions))

    def get_ir(self):
        return "main:\n\t" + '\n\t'.join(map(str, self.funcs))


class IRFunc:
    """
    IR Function Container
    """

    def __init__(self, name: str, param_info: ParamInfo, instructions: [BaseIRStr]):
        self.name = name
        self.paramInfo = param_info
        self.instructions = instructions
