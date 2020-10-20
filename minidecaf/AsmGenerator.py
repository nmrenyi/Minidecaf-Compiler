from minidecaf.IRContainer import IRContainer
from minidecaf.AsmWriter import AsmWriter
from minidecaf.IRStr import BaseIRStr
from minidecaf.AsmCommand import AsmDirective
from minidecaf.AsmCommand import AsmLabel
from minidecaf.AsmCommand import AsmInstruction
from minidecaf.AsmCommand import AsmInstructionList
from minidecaf.utils import push_reg, push_int, pop

class AsmGenerator:
    '''
    Asm Command Generator
    generate asm commands from IR
    '''
    def __init__(self, asmWriter:AsmWriter):
        self.writer = asmWriter

    def checkConflict(self, globs, funcs, funcDecl):
        var_name_list = [glob.var.name for glob in globs]
        funcs_name_list = [func.name for func in funcs]
        conflict = list(set(var_name_list) & (set(funcs_name_list) | set(funcDecl)))
        if len(conflict) != 0:
            raise Exception('conflict naming between global var and func')

    def generate(self, ir:IRContainer):
        self.ir = ir
        self.checkConflict(ir.globs, ir.funcs, ir.funcDecl)
        for glob in ir.globs:
            if glob.init is None:
                self.writer.writeList([AsmDirective(f".comm {glob.var.name},{glob.size},4")])
            else:
                self.writer.writeList([
                    AsmDirective(".data"),
                    AsmDirective(f".globl {glob.var.name}"),
                    AsmDirective(f".align 4"),
                    AsmDirective(f".size {glob.var.name}, {glob.size}"),
                    AsmLabel(f"{glob.var.name}"),
                    AsmDirective(f".quad {glob.init}")])

        for func in ir.funcs:
            self.curFunc = func.name
            self.generateHeader(f"{func.name}", func.paramInfo)
            self.generateFromIRList(func.instructions)
            self.generateEpilogue(f"{func.name}")

        # self.generateHeader('main')
        # self.generateFromIR(ir)
        # self.generateEpilogue("main")


    def generateHeader(self, func_name:str, paramInfo):
        self.writer.writeList([
            AsmDirective(".text"),
            AsmDirective(f".globl {func_name}"),
            AsmLabel(f'{func_name}')] + 
            AsmInstructionList(push_reg('ra')).__str__().split('\n') + 
            AsmInstructionList(push_reg('fp')).__str__().split('\n') +
            [AsmInstruction('mv fp, sp')])

        for i in range(paramInfo.paramNum):
            fr, to = 4 * (i + 2), - 8 * (i + 1)
            self.writer.writeList([
                AsmInstruction(f"lw t1, {fr}(fp)")] +
                AsmInstructionList(push_reg('t1')).__str__().split('\n'))
            
    def generateEpilogue(self, func:str):
        self.writer.writeList(
            AsmInstructionList(push_int(0)).__str__().split('\n') + # push 0 for no return status, default return 0
            [
                AsmLabel(f"{func}_exit"),
                AsmInstruction("lw a0, 0(sp)"),
                AsmInstruction("mv sp, fp")] +
                AsmInstructionList(pop("fp")).__str__().split('\n') + 
                AsmInstructionList(pop('ra')).__str__().split('\n') + [
                AsmInstruction("jr ra"),
            ])

    def generateFromIRList(self, irList):
        commandList = [AsmInstructionList(ir.genAsm()) for ir in irList]
        self.writer.writeList(commandList)

    def generateFromIR(self, irContainer:IRContainer):
        commandList = [AsmInstructionList(ir.genAsm()) for ir in irContainer.ir_str_list]
        self.writer.writeList(commandList)

    def generateReturn(self):
        self.writer.write(AsmInstruction("jr ra"))
