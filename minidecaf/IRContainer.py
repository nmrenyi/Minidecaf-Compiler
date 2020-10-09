import minidecaf.IRStr
class IRContainer:
    '''
    A List Containing IR string, with add method
    __str__ method returns the string representation of IR
    '''
    def __init__(self):
        self.ir_str_list = []
    
    def __str__(self):
        return "main:\n\t" + '\n\t'.join(map(str, self.ir_str_list))

    def add(self, ir:minidecaf.IRStr.BaseIRStr):
        self.ir_str_list.append(ir)
    def addList(self, irList):
        self.ir_str_list.extend(irList)
    # def getIR(self):
    #     return "main:\n\t" + '\n\t'.join(map(str, self.ir_str_list))
