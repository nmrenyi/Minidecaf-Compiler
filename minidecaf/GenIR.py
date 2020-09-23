from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
import minidecaf.IRStr as IRStr

class GenIR(MiniDecafVisitor):
    def __init__(self, irContainer):
        self._container = irContainer
    
    def visitReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        self.visitChildren(ctx)
        self._container.add(IRStr.Ret())

    def visitExpr(self, ctx:MiniDecafParser.ExprContext):
        v = int(ctx.Integer().getText())
        self._container.add(IRStr.Const(v))
