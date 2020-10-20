# MiniDecaf Compiler Authored by Ren Yi 2018011423
# The general structure references to TA's implementation.

import argparse
import sys

import antlr4

from minidecaf.AsmGenerator import AsmGenerator
from minidecaf.AsmWriter import AsmWriter
from minidecaf.IRContainer import IRContainer
from minidecaf.IRGenerator import IRGenerator
from minidecaf.NameParser import NameParser
from minidecaf.typer import Typer
from .generated.MiniDecafLexer import MiniDecafLexer
from .generated.MiniDecafParser import MiniDecafParser


def parse_args(argv):
    parser = argparse.ArgumentParser(description="MiniDecaf compiler by RenYi 2018011423")
    parser.add_argument("infile", type=str,
                        help="the input C file")
    parser.add_argument("outfile", type=str, nargs="?",
                        help="the output assembly file")
    parser.add_argument("-ir", action="store_true", help="emit ir rather than asm")
    return parser.parse_args()


def my_parser(token_stream):
    parser = MiniDecafParser(token_stream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree = parser.prog()
    return tree


def my_lexer(input_stream):
    lexer = MiniDecafLexer(input_stream)
    token_stream = antlr4.CommonTokenStream(lexer)
    return token_stream


def gen_ir(tree, nameManager, typeInfo):
    ir_container = IRContainer()
    IRGenerator(ir_container, nameManager, typeInfo).visit(tree)
    return ir_container


def gen_asm(ir: IRContainer, output_file):
    if output_file is None:  # >out.S as command line instruction
        asm_writer = AsmWriter(sys.stdout)
    else:  # out.S as command line instruction
        with open(output_file, 'w') as fout:
            asm_writer = AsmWriter(fout)

    asm_generator = AsmGenerator(asm_writer)
    asm_generator.generate(ir)
    asm_writer.close()


def name_parse(tree):
    name_parser = NameParser()
    name_parser.visit(tree)
    return name_parser.funcNameManager


def check_type(tree, name_info):
    type_checker = Typer(name_info)
    type_checker.visit(tree)
    return type_checker.typeInfo


def main():
    args = parse_args(sys.argv)
    input_stream = antlr4.FileStream(args.infile)
    token_stream = my_lexer(input_stream)
    tree = my_parser(token_stream)
    name_manager = name_parse(tree)
    type_info = check_type(tree, name_manager)
    ir = gen_ir(tree, name_manager, type_info)
    if args.ir:
        print(ir)
    else:
        gen_asm(ir, args.outfile)
