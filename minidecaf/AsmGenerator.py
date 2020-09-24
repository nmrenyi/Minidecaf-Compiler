from minidecaf.IRContainer import IRContainer
from minidecaf.AsmWriter import AsmWriter
from minidecaf.IRStr import BaseIRStr
from minidecaf.AsmCommand import AsmDirective
from minidecaf.AsmCommand import AsmLabel
from minidecaf.AsmCommand import AsmInstruction
from minidecaf.AsmCommand import AsmInstructionList

class AsmGenerator:
    '''
    Asm Command Generator
    generate asm commands from IR
    '''
    def __init__(self, asmWriter:AsmWriter):
        self.writer = asmWriter

    def generate(self, ir:IRContainer):
        self.generateHeader()
        self.generateFromIR(ir)
        self.generateReturn()

    def generateHeader(self):
        self.writer.writeList([
            AsmDirective(".text"),
            AsmDirective(".globl main"),
            AsmLabel("main")])
    
    def generateFromIR(self, irContainer:IRContainer):
        commandList = [AsmInstructionList(ir.genAsm()) for ir in irContainer.ir_str_list]
        self.writer.writeList(commandList)

    def generateReturn(self):
        self.writer.write(AsmInstruction("jr ra"))
