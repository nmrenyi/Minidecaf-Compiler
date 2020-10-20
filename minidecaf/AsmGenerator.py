from minidecaf.AsmCommand import AsmDirective
from minidecaf.AsmCommand import AsmInstruction
from minidecaf.AsmCommand import AsmInstructionList
from minidecaf.AsmCommand import AsmLabel
from minidecaf.AsmWriter import AsmWriter
from minidecaf.IRContainer import IRContainer
from minidecaf.utils import push_reg, push_int, pop


class AsmGenerator:
    """
    Asm Command Generator
    generate asm commands from IR
    """

    def __init__(self, asm_writer: AsmWriter):
        self.writer = asm_writer

    def check_conflict(self, globs, funcs, func_decl):
        var_name_list = [glob.var.name for glob in globs]
        funcs_name_list = [func.name for func in funcs]
        conflict = list(set(var_name_list) & (set(funcs_name_list) | set(func_decl)))
        if len(conflict) != 0:
            raise Exception('conflict naming between global var and func')

    def generate(self, ir: IRContainer):
        self.ir = ir
        self.check_conflict(ir.globs, ir.funcs, ir.funcDecl)
        for glob in ir.globs:
            if glob.init is None:
                self.writer.write_list([AsmDirective(f".comm {glob.var.name},{glob.size},4")])
            else:
                self.writer.write_list([
                    AsmDirective(".data"),
                    AsmDirective(f".globl {glob.var.name}"),
                    AsmDirective(f".align 4"),
                    AsmDirective(f".size {glob.var.name}, {glob.size}"),
                    AsmLabel(f"{glob.var.name}"),
                    AsmDirective(f".quad {glob.init}")])

        for func in ir.funcs:
            self.curFunc = func.name
            self.generate_header(f"{func.name}", func.paramInfo)
            self.generate_from_ir_list(func.instructions)
            self.generate_epilogue(f"{func.name}")

        # self.generateHeader('main')
        # self.generateFromIR(ir)
        # self.generateEpilogue("main")

    def generate_header(self, func_name: str, param_info):
        self.writer.write_list([
                                  AsmDirective(".text"),
                                  AsmDirective(f".globl {func_name}"),
                                  AsmLabel(f'{func_name}')] +
                               AsmInstructionList(push_reg('ra')).__str__().split('\n') +
                               AsmInstructionList(push_reg('fp')).__str__().split('\n') +
                               [AsmInstruction('mv fp, sp')])

        for i in range(param_info.paramNum):
            fr, to = 4 * (i + 2), - 8 * (i + 1)
            self.writer.write_list([
                                      AsmInstruction(f"lw t1, {fr}(fp)")] +
                                   AsmInstructionList(push_reg('t1')).__str__().split('\n'))

    def generate_epilogue(self, func: str):
        self.writer.write_list(
            AsmInstructionList(push_int(0)).__str__().split('\n') +  # push 0 for no return status, default return 0
            [
                AsmLabel(f"{func}_exit"),
                AsmInstruction("lw a0, 0(sp)"),
                AsmInstruction("mv sp, fp")] +
            AsmInstructionList(pop("fp")).__str__().split('\n') +
            AsmInstructionList(pop('ra')).__str__().split('\n') + [
                AsmInstruction("jr ra"),
            ])

    def generate_from_ir_list(self, ir_list):
        command_list = [AsmInstructionList(ir.gen_asm()) for ir in ir_list]
        self.writer.write_list(command_list)

    def generate_from_ir(self, ir_container: IRContainer):
        command_list = [AsmInstructionList(ir.gen_asm()) for ir in ir_container.ir_str_list]
        self.writer.write_list(command_list)

    def generate_return(self):
        self.writer.write(AsmInstruction("jr ra"))
