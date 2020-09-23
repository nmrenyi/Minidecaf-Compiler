import antlr4
from .generated.MiniDecafLexer import MiniDecafLexer
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor
from minidecaf.IRContainer import IRContainer
from minidecaf.GenIR import GenIR

def Parser(tokenStream):
    parser = MiniDecafParser(tokenStream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree = parser.prog()
    return tree

def Lexer(inputStream):
    lexer = MiniDecafLexer(inputStream)
    tokenStream = antlr4.CommonTokenStream(lexer)
    return tokenStream

def irGenerator(tree):
    irContainer = IRContainer()
    GenIR(irContainer).visit(tree)
    return irContainer.getIR()


def main():
    inputStream = antlr4.FileStream('multi_digit.c')
    tokenStream = Lexer(inputStream)
    tree = Parser(tokenStream)
    ir = irGenerator(tree)
    print(ir)
    # print("""\
    #         .text
    #         .globl  main
    # main:
    #         li      a0,123
    #         ret\
    # """)
