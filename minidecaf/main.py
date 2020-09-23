import antlr4
from .generated.MiniDecafLexer import MiniDecafLexer
from .generated.MiniDecafParser import MiniDecafParser

def Parser(tokenStream):
    parser = MiniDecafParser(tokenStream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree = parser.prog()
    return tree

def main():
    inputStream = antlr4.FileStream('multi_digit.c')
    print(inputStream)
    # tokenStream = antlr4.Lexer(inputStream)
    # tree = Parser(tokenStream)

    # print("""\
    #         .text
    #         .globl  main
    # main:
    #         li      a0,123
    #         ret\
    # """)
