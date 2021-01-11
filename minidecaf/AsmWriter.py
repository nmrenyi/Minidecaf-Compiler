from minidecaf.AsmCommand import AsmCommand


class AsmWriter:
    """
    a writer for asm commands
    self.f can be sys.stdout or a file handler
    """

    def __init__(self, out_file):
        self.f = out_file

    def write(self, command: AsmCommand):
        print(f'{command}', file=self.f)

    def write_list(self, commands: [AsmCommand]):
        for command in commands:
            self.write(command)

    def close(self):
        self.f.close()
