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
    
    def generate(self, ir:IRContainer):
        self.generateHeader('main')
        self.generateFromIR(ir)
        self.generateReturn()
        self.generateEpilogue("main")


    def generateHeader(self, func_name:str):
        self.writer.writeList([
            AsmDirective(".text"),
            AsmDirective(f".globl {func_name}"),
            AsmLabel(f'{func_name}')] + 
            push_reg('ra') + push_reg('fp') +
            [AsmInstruction('mv fp, sp')
            ])
    def generateEpilogue(self, func:str):
        self.writer.writeList(
            push_int(0) + [
            AsmLabel(f"{func}_exit"),
            AsmInstruction("lw a0, 0(sp)"),
            AsmInstruction("mv sp, fp")] +
            pop("fp") + pop('ra') + [
            AsmInstruction("jr ra"),
            ])

    def generateFromIR(self, irContainer:IRContainer):
        commandList = [AsmInstructionList(ir.genAsm()) for ir in irContainer.ir_str_list]
        self.writer.writeList(commandList)

    def generateReturn(self):
        self.writer.write(AsmInstruction("jr ra"))
