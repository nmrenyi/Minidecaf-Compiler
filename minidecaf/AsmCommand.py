# These Command Structures are copied from TA's reference implementations.
# They have very clear structure and good scalability. So I used them directly in my step1.

class AsmCommand:
    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return self.__str__()


class AsmLabel(AsmCommand):
    def __str__(self):
        return f"{self.s}:"

class AsmInstruction(AsmCommand):
    def __str__(self):
        return f"\t{self.s}"

class AsmInstructionList(AsmCommand):
    def __str__(self):
        # self.s is a list of str
        local_s = ''
        for string in self.s:
            local_s += '\t' + string + '\n'
        return local_s

class AsmDirective(AsmCommand):
    def __str__(self):
        return f"\t{self.s}"
