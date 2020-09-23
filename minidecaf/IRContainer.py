class IRContainer:
    def __init__(self):
        self.ir_str_list = []

    def add(self, ir):
        self.ir_str_list.append(ir)

    def getIR(self):
        return "main:\n\t" + '\n\t'.join(map(str, self.ir_str_list))
