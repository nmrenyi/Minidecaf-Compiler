# These Command Structures are copied from TA's reference implementations.
# They have very clear structure and good scalability. So I used them directly in my step1 as a good starting structure.

class AsmCommand:
    '''
    base class for asm commands
    '''
    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return self.__str__()


class AsmLabel(AsmCommand):
    '''
    represent labels like 'main'
    '''
    def __str__(self):
        return f"{self.s}:"

class AsmInstruction(AsmCommand):
    '''
    represent instructions like 'jr ra'
    '''
    def __str__(self):
        return f"\t{self.s}"

class AsmInstructionList(AsmCommand):
    '''
    concatenate instructions in the list
    '''
    def __str__(self):
        # self.s is a list of str
        local_s = ''
        for string in self.s:
            local_s += '\t' + string + '\n'
        return local_s

class AsmDirective(AsmCommand):
    '''
    asm directives like '.globl', '.text'
    '''
    def __str__(self):
        return f"\t{self.s}"
