from minidecaf.AsmCommand import AsmCommand
class AsmWriter:
    '''
    a writer for asm commands
    self.f can be sys.stdout or a file handler
    '''
    def __init__(self, fout):
        self.f = fout
    
    def write(self, command: AsmCommand):
        print(f'{command}', file = self.f)
    
    def writeList(self, commands: [AsmCommand]):
        for command in commands:
            self.write(command)
    
    def close(self):
        self.f.close()