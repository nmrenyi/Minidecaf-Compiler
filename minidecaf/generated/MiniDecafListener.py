# Generated from MiniDecaf.g4 by ANTLR 4.8
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .MiniDecafParser import MiniDecafParser
else:
    from MiniDecafParser import MiniDecafParser

# This class defines a complete listener for a parse tree produced by MiniDecafParser.
class MiniDecafListener(ParseTreeListener):

    # Enter a parse tree produced by MiniDecafParser#prog.
    def enterProg(self, ctx:MiniDecafParser.ProgContext):
        pass

    # Exit a parse tree produced by MiniDecafParser#prog.
    def exitProg(self, ctx:MiniDecafParser.ProgContext):
        pass


    # Enter a parse tree produced by MiniDecafParser#func.
    def enterFunc(self, ctx:MiniDecafParser.FuncContext):
        pass

    # Exit a parse tree produced by MiniDecafParser#func.
    def exitFunc(self, ctx:MiniDecafParser.FuncContext):
        pass


    # Enter a parse tree produced by MiniDecafParser#ty.
    def enterTy(self, ctx:MiniDecafParser.TyContext):
        pass

    # Exit a parse tree produced by MiniDecafParser#ty.
    def exitTy(self, ctx:MiniDecafParser.TyContext):
        pass


    # Enter a parse tree produced by MiniDecafParser#returnStmt.
    def enterReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        pass

    # Exit a parse tree produced by MiniDecafParser#returnStmt.
    def exitReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        pass


    # Enter a parse tree produced by MiniDecafParser#expr.
    def enterExpr(self, ctx:MiniDecafParser.ExprContext):
        pass

    # Exit a parse tree produced by MiniDecafParser#expr.
    def exitExpr(self, ctx:MiniDecafParser.ExprContext):
        pass



del MiniDecafParser