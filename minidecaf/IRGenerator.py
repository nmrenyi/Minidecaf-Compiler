from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
import minidecaf.IRStr as IRStr

class IRGenerator(MiniDecafVisitor):
    '''
    A visitor for going through the whole ast, inherited from MiniDecafVisitor
    The accept method in different node uses the vistor's different methods, that is the visitor pattern.
    '''
    def __init__(self, irContainer):
        self._container = irContainer
    
    def visitReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        # be careful of the relative position(i.e. order) of these two commands
        self.visitChildren(ctx)
        self._container.add(IRStr.Ret())

    def visitExpr(self, ctx:MiniDecafParser.ExprContext):
        # what if the expression not a simple integer, but a function or arithmetic expression like (1+2)?
        v = int(ctx.Integer().getText())
        self._container.add(IRStr.Const(v))


