from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
import minidecaf.IRStr as IRStr

class OffsetTable(object):
    '''
    Referenced to TA's OffsetManager
    This class aims to note the offset value of every identifier.
    '''
    def __init__(self):
        self._off = {}
        self._top = 0

    def __getitem__(self, var):
        return self._off[var]

    def newSlot(self, var=None):
        self._top -= 4
        if var is not None:
            self._off[var] = self._top
        return self._top


class IRGenerator(MiniDecafVisitor):
    '''
    A visitor for going through the whole ast, inherited from MiniDecafVisitor
    The accept method in different node uses the vistor's different methods, that is the visitor pattern.
    '''
    def __init__(self, irContainer):
        self._container = irContainer
        self.offsetTable = OffsetTable()
    
    def visitReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        # be careful of the relative position(i.e. order) of these two commands
        self.visitChildren(ctx)
        self._container.add(IRStr.Ret())

    def visitExprStmt(self, ctx:MiniDecafParser.ExprStmtContext):
        self.visitChildren(ctx)
        self._container.add(IRStr.Pop())

    def visitExpr(self, ctx:MiniDecafParser.ExprContext):
        self.visitChildren(ctx)

    def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if ctx.expr() is not None:
                ctx.expr().accept(self) # get expression value
            else:
                self._container.add(IRStr.Const(0)) # default value is zero
            self.offsetTable.newSlot(var) # new stack space for var
    
    def visitWithAsgn(self, ctx:MiniDecafParser.WithAsgnContext):
        ctx.assignment().accept(self)
        if ctx.Ident() is not None:
            self._container.add(IRStr.FrameSlot(self.offsetTable[ctx.Ident().getText()]))
        else:
            raise Exception('Identifier Not Found')
        # self._computeAddr(ctx.unary())
        self._container.add(IRStr.Store())

    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        self._container.add(IRStr.FrameSlot(self.offsetTable[ctx.Ident().getText()]))
        self._container.add(IRStr.Load())

    def visitUnary(self, ctx:MiniDecafParser.UnaryContext):
        self.visitChildren(ctx)
        if ctx.unaryOp() is not None:
            self._container.add(IRStr.Unary(ctx.unaryOp().getText()))
    
    def visitAtomInteger(self, ctx:MiniDecafParser.AtomIntegerContext):
        # no children in atomInteger branch, get the Integer DIRECTLY
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
    