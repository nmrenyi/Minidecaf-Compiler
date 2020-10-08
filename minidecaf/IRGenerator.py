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
        self.visitChildren(ctx)
        # v = int(ctx.Integer().getText())
        # self._container.add(IRStr.Const(v))

    def visitUnary(self, ctx:MiniDecafParser.UnaryContext):
        self.visitChildren(ctx)
        if ctx.unaryOp() is not None:
            self._container.add(IRStr.Unary(ctx.unaryOp().getText()))
    
    def visitIntUnit(self, ctx:MiniDecafParser.IntUnitContext):
        self.visitChildren(ctx)
        if ctx.Integer() is not None:
            v = int(ctx.Integer().getText())
            self._container.add(IRStr.Const(v))

    def visitAdditive(self, ctx:MiniDecafParser.AdditiveContext):
        self.visitChildren(ctx)
        if ctx.addOp() is not None:
            self._container.add(IRStr.Binary(ctx.addOp().getText()))
    
    def visitMultiplicative(self, ctx:MiniDecafParser.MultiplicativeContext):
        self.visitChildren(ctx)
        if ctx.mulOp() is not None:
            self._container.add(IRStr.Binary(ctx.mulOp().getText()))

    def visitLogicalAnd(self, ctx:MiniDecafParser.LogicalAndContext):
        self.visitChildren(ctx)
        if ctx.andOp() is not None:
            self._container.add(IRStr.Binary(ctx.andOp().getText()))

    def visitLogicalOr(self, ctx:MiniDecafParser.LogicalOrContext):
        self.visitChildren(ctx)
        if ctx.orOp() is not None:
            self._container.add(IRStr.Binary(ctx.orOp().getText()))

    def visitRelational(self, ctx:MiniDecafParser.RelationalContext):
        self.visitChildren(ctx)
        if ctx.relOp() is not None:
            self._container.add(IRStr.Binary(ctx.relOp().getText()))
    
    def visitEquality(self, ctx:MiniDecafParser.EqualityContext):
        self.visitChildren(ctx)
        if ctx.eqOp() is not None:
            self._container.add(IRStr.Binary(ctx.eqOp().getText()))
    
            

    
