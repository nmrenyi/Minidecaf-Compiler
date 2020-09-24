from minidecaf.AsmCommand import AsmCommand
class AsmWriter:
    def __init__(self, output_file:str):
        self.f = open(output_file, 'w', encoding='utf-8')
    
    def write(self, command: AsmCommand):
        print(f'{command}', file = self.f)
    
    def writeList(self, commands: [AsmCommand]):
        for command in commands:
            self.write(command)
    
    def close(self):
        self.f.close()
