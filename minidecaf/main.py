import antlr4
import sys
from .generated.MiniDecafLexer import MiniDecafLexer
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor
from minidecaf.IRContainer import IRContainer
from minidecaf.IRGenerator import IRGenerator
from minidecaf.AsmWriter import AsmWriter
from minidecaf.AsmGenerator import AsmGenerator

def Parser(tokenStream):
    parser = MiniDecafParser(tokenStream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree = parser.prog()
    return tree

def Lexer(inputStream):
    lexer = MiniDecafLexer(inputStream)
    tokenStream = antlr4.CommonTokenStream(lexer)
    return tokenStream

def GenIR(tree):
    irContainer = IRContainer()
    IRGenerator(irContainer).visit(tree)
    return irContainer

def GenAsm(ir:IRContainer, output_file:str):
    asmWriter = AsmWriter(output_file)
    asmGenerator = AsmGenerator(asmWriter)
    asmGenerator.generate(ir)
    asmWriter.close()

def main():
    inputStream = antlr4.FileStream('multi_digit.c')
    tokenStream = Lexer(inputStream)
    tree = Parser(tokenStream)
    ir = GenIR(tree)
    print(ir)
    GenAsm(ir, 'myFirstAsm.S')
