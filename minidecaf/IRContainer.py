import minidecaf.IRStr
class IRContainer:
    '''
    A List Containing Irs, with add method
    '''
    def __init__(self):
        self.ir_str_list = []
    
    def __str__(self):
        # print(self.instrs)
        return "main:\n\t" + '\n\t'.join(map(str, self.ir_str_list))

    def add(self, ir:minidecaf.IRStr.BaseIRStr):
        self.ir_str_list.append(ir)

    # def getIR(self):
    #     return "main:\n\t" + '\n\t'.join(map(str, self.ir_str_list))
