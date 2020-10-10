# MiniDecaf Compiler Authored by Ren Yi 2018011423
# The general structure references to TA's implementation.

import antlr4
import sys
import argparse
from .generated.MiniDecafLexer import MiniDecafLexer
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor
from minidecaf.IRContainer import IRContainer
from minidecaf.IRGenerator import IRGenerator
from minidecaf.AsmWriter import AsmWriter
from minidecaf.AsmGenerator import AsmGenerator
from minidecaf.NameParser import NameParser
def parseArgs(argv):
    parser = argparse.ArgumentParser(description="MiniDecaf compiler by RenYi 2018011423")
    parser.add_argument("infile", type=str,
                       help="the input C file")
    parser.add_argument("outfile", type=str, nargs="?",
                       help="the output assembly file")
    parser.add_argument("-ir", action="store_true", help="emit ir rather than asm")
    return parser.parse_args()

def Parser(tokenStream):
    parser = MiniDecafParser(tokenStream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree = parser.prog()
    return tree

def Lexer(inputStream):
    lexer = MiniDecafLexer(inputStream)
    tokenStream = antlr4.CommonTokenStream(lexer)
    return tokenStream

def GenIR(tree, nameManager):
    irContainer = IRContainer()
    IRGenerator(irContainer, nameManager).visit(tree)
    return irContainer

def GenAsm(ir:IRContainer, output_file):
    if output_file is None: # >out.S as command line instruction
        asmWriter = AsmWriter(sys.stdout)
    else: # out.S as command line instruction
        with open(output_file, 'w') as fout:
            asmWriter = AsmWriter(fout)

    asmGenerator = AsmGenerator(asmWriter)
    asmGenerator.generate(ir)
    asmWriter.close()

def NameParse(tree):
    nameParser = NameParser()
    nameParser.visit(tree)
    return nameParser.nameManager

def main():
    args = parseArgs(sys.argv)
    inputStream = antlr4.FileStream(args.infile)
    tokenStream = Lexer(inputStream)
    tree = Parser(tokenStream)
    nameManager = NameParse(tree)
    ir = GenIR(tree, nameManager)
    if args.ir:
        print(ir)
    else:
        GenAsm(ir, args.outfile)
