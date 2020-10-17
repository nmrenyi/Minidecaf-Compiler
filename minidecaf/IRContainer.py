import minidecaf.IRStr
from minidecaf.NameParser import ParamInfo
from minidecaf.IRStr import BaseIRStr

class IRContainer:
    '''
    A List Containing IR string, with add method
    __str__ method returns the string representation of IR
    '''
    def __init__(self):
        self.curInstrs = []
        self.curName = None
        self.curParamInfo = None
        self.funcs = []
        self.globs = []
        self.funcDecl = []

    def __str__(self):
        return "main:\n\t" + '\n\t'.join(map(str, self.curInstrs))

    def add(self, ir:minidecaf.IRStr.BaseIRStr):
        self.curInstrs.append(ir)
    def addFuncDecl(self, decl:str):
        self.funcDecl.append(decl)

    def addList(self, irList):
        self.curInstrs.extend(irList)

    def addGlobal(self, globalInfo):
        assert globalInfo.var.offset is None
        self.globs.append(globalInfo)

    def enterFunction(self, name:str, paramInfo):
        self.curName = name
        self.curParamInfo = paramInfo
        self.curInstrs = []

    def exitFunction(self):
        self.funcs.append(IRFunc(self.curName, self.curParamInfo, self.curInstrs))

    def getIR(self):
        return "main:\n\t" + '\n\t'.join(map(str, self.funcs))

class IRFunc:
    '''
    IR Function Container
    '''
    def __init__(self, name:str, paramInfo:ParamInfo, instrs:[BaseIRStr]):
        self.name = name
        self.paramInfo = paramInfo
        self.instrs = instrs
