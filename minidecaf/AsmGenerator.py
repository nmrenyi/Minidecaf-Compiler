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
        self.generateEpilogue("main")


    def generateHeader(self, func_name:str):
        self.writer.writeList([
            AsmDirective(".text"),
            AsmDirective(f".globl {func_name}"),
            AsmLabel(f'{func_name}')] + 
            AsmInstructionList(push_reg('ra')).__str__().split('\n') + 
            AsmInstructionList(push_reg('fp')).__str__().split('\n') +
            [AsmInstruction('mv fp, sp')
            ])
            
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

    def generateFromIR(self, irContainer:IRContainer):
        commandList = [AsmInstructionList(ir.genAsm()) for ir in irContainer.ir_str_list]
        self.writer.writeList(commandList)

    def generateReturn(self):
        self.writer.write(AsmInstruction("jr ra"))
