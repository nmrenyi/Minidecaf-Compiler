"""
MiniDecaf Compiler Authored by Ren Yi 2018011423
The general structure references to TA's implementation.
"""
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


def parse_args():
    """
    arg parser for command line
    Reference to TA's implementation
    """
    parser = argparse.ArgumentParser(description="MiniDecaf compiler by RenYi 2018011423")
    parser.add_argument("infile", type=str,
                        help="the input C file")
    parser.add_argument("outfile", type=str, nargs="?",
                        help="the output assembly file")
    parser.add_argument("-ir", action="store_true", help="emit ir rather than asm")
    return parser.parse_args()


def my_parser(token_stream):
    """
    Parser function with call to auto generated parser

    :param token_stream:
    :return ast_tree:
    """
    parser = MiniDecafParser(token_stream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree = parser.prog()
    return tree


def my_lexer(input_stream):
    """
    Lexer function with call to auto generated lexer
    :param input_stream:
    :return token_stream:
    """
    lexer = MiniDecafLexer(input_stream)
    token_stream = antlr4.CommonTokenStream(lexer)
    return token_stream


def gen_ir(tree, name_manager, type_info):
    """
    generate intermediate representation for the input C file

    :param tree:
    :param name_manager:
    :param type_info:
    :return ir_container:
    """
    ir_container = IRContainer()
    IRGenerator(ir_container, name_manager, type_info).visit(tree)
    return ir_container


def gen_asm(ir: IRContainer, output_file):
    """
    Assembly generator from IR
    :param ir:
    :param output_file:
    """
    if output_file is None:  # >out.S as command line instruction
        asm_writer = AsmWriter(sys.stdout)
    else:  # out.S as command line instruction
        with open(output_file, 'w') as out_file:
            asm_writer = AsmWriter(out_file)

    asm_generator = AsmGenerator(asm_writer)
    asm_generator.generate(ir)
    asm_writer.close()


def name_parse(tree):
    """
    name parsing for AST
    :param tree:
    :return:
    """
    name_parser = NameParser()
    name_parser.visit(tree)
    return name_parser.funcNameManager


def check_type(tree, name_info):
    """
    type check for ast
    :param tree:
    :param name_info:
    :return:
    """
    type_checker = Typer(name_info)
    type_checker.visit(tree)
    return type_checker.typeInfo


def main():
    """
    Main entry for minidecaf parser

    :return:
    """
    args = parse_args()
    input_stream = antlr4.FileStream(args.infile)
    token_stream = my_lexer(input_stream)
    tree = my_parser(token_stream)
    name_manager = name_parse(tree)
    type_info = check_type(tree, name_manager)
    ir = gen_ir(tree, name_manager, type_info)
    if args.ir:
        print(ir)  # easy for debugging using intermediate representation
    else:
        gen_asm(ir, args.outfile)
