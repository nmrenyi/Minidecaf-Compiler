from ast import literal_eval

from minidecaf.IRStr import *
from minidecaf.types import *
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor


class TypeInfo:
    """
    type parse only takes effect on expressions
    """
    def __init__(self):
        self.loc = {}  # ExprContext -> (IRInstr|ExprContext)+
        self.funcs = {}  # str -> FuncTypeInfo
        self.term2type = {}  # ExprContext -> Type

    def lvalueLoc(self, ctx):
        return self.loc[ctx]

    def setLvalueLoc(self, ctx, loc: list):
        self.loc[ctx] = loc

    def __getitem__(self, ctx):
        return self.term2type[ctx]


class FuncTypeInfo:
    """
    the function type manager
    stores the function return value type and the parameter types
    """
    def __init__(self, retTy: Type, paramTy: list):
        self.retTy = retTy
        self.paramTy = paramTy

    def compatible(self, other):
        return self.retTy == other.retTy and self.paramTy == other.paramTy

    def call(self):
        @TypeRule
        def callRule(ctx, argTy: list):
            if self.paramTy == argTy:
                return self.retTy
            return f"bad argument types"
        return callRule


def save_type(f):
    """
    decorator mode
    note down the type information in a dict
    :param f:
    :return:
    """
    def g(self, ctx):
        ty = f(self, ctx)
        self.typeInfo.term2type[ctx] = ty
        return ty

    return g


class Typer(MiniDecafVisitor):
    """
    Type checking.
    Run after name resolution, type checking computes the type of each
    expression, and also check for incompatibilities like int*+int*. Besides
    type checking, Typer also does lvalue analysis i.e. determine which
    expressions are lvalues and their address.

    Reference to TA's implementation
    """

    def __init__(self, nameInfo):
        self.var2type = {}  # Variable -> Type
        self.nameInfo = nameInfo # FuncInfo Object
        self.curFunc = None
        self.typeInfo = TypeInfo()
        self.locator = Locator(self.nameInfo, self.typeInfo)

    def visitChildren(self, ctx):
        ty = MiniDecafVisitor.visitChildren(self, ctx) # return the type object in types.py (visitors has been
        # reimplemented in this class)
        self.typeInfo.term2type[ctx] = ty
        return ty

    def _var(self, term):
        return self.nameInfo[term]

    def _declTyp(self, ctx: MiniDecafParser.DeclarationContext):
        """
        :param ctx:
        :return: corresponding type to the declaration
        """
        base = ctx.ty().accept(self)
        dims = [int(x.getText()) for x in reversed(ctx.Integer())]
        if len(dims) == 0:
            return base
        else:
            return ArrayType.make(base, dims)

    def _funcTypeInfo(self, ctx):
        retTy = ctx.ty().accept(self)
        paramTy = self.paramTy(ctx.paramList())
        return FuncTypeInfo(retTy, paramTy)

    def _argTy(self, ctx: MiniDecafParser.ArgListContext):
        return list(map(lambda x: x.accept(self), ctx.expr()))

    def visitPtrType(self, ctx: MiniDecafParser.PtrTypeContext):
        return PtrType(ctx.ty().accept(self))

    def visitIntType(self, ctx: MiniDecafParser.IntTypeContext):
        return IntType()

    def locate(self, ctx):
        loc = self.locator.locate(self.curFunc, ctx)
        if loc is None:
            raise Exception(ctx, "lvalue expected")
        self.typeInfo.setLvalueLoc(ctx, loc)

    def checkUnary(self, ctx, op: str, ty: Type):
        """
        return the op's corresponding rule
        :param ctx:
        :param op:
        :param lhs: left hand side type
        :param rhs: right hand side type
        """
        rule = expandIterableKey([
            (['-', '!', '~'], intUnaopRule),
            (['&'], addrofRule),
            (['*'], derefRule),
        ])[op]
        return rule(ctx, ty)

    def checkBinary(self, ctx, op: str, lhs: Type, rhs: Type):
        """
        return the op's corresponding rule
        :param ctx:
        :param op:
        :param lhs: left hand side type
        :param rhs: right hand side type
        :return:
        """
        rule = expandIterableKey([
            (['*', '/', '%'] + ["&&", "||"], intBinopRule),
            (["==", "!="], eqRule),
            (["<", "<=", ">", ">="], relRule),
            (['='], asgnRule),
            (['+'], tryEach('+', intBinopRule, ptrArithRule)),
            (['-'], tryEach('-', intBinopRule, ptrArithRule, ptrDiffRule)),
        ])[op]
        return rule(ctx, lhs, rhs)

    @save_type
    def visitCCast(self, ctx: MiniDecafParser.CCastContext):
        ctx.cast().accept(self)
        return ctx.ty().accept(self)

    @save_type
    def visitCUnary(self, ctx: MiniDecafParser.CUnaryContext):
        res = self.checkUnary(ctx.unaryOp(), ctx.unaryOp().getText(),
                              ctx.cast().accept(self))
        if ctx.unaryOp().getText() == '&':
            self.locate(ctx.cast())
        return res

    @save_type
    def visitAtomParen(self, ctx: MiniDecafParser.AtomParenContext):
        return ctx.expr().accept(self)

    @save_type
    def visitCAdd(self, ctx: MiniDecafParser.CAddContext):
        return self.checkBinary(ctx.addOp(), ctx.addOp().getText(),
                                ctx.additive().accept(self), ctx.multiplicative().accept(self))

    @save_type
    def visitCMul(self, ctx: MiniDecafParser.CMulContext):
        return self.checkBinary(ctx.mulOp(), ctx.mulOp().getText(),
                                ctx.multiplicative().accept(self), ctx.cast().accept(self))

    @save_type
    def visitCRel(self, ctx: MiniDecafParser.CRelContext):
        return self.checkBinary(ctx.relOp(), ctx.relOp().getText(),
                                ctx.relational().accept(self), ctx.additive().accept(self))

    @save_type
    def visitCEq(self, ctx: MiniDecafParser.CEqContext):
        return self.checkBinary(ctx.eqOp(), ctx.eqOp().getText(),
                                ctx.equality().accept(self), ctx.relational().accept(self))

    @save_type
    def visitCLand(self, ctx: MiniDecafParser.CLandContext):
        return self.checkBinary(ctx, "&&",
                                ctx.logicalAnd().accept(self), ctx.equality().accept(self))

    @save_type
    def visitCLor(self, ctx: MiniDecafParser.CLorContext):
        return self.checkBinary(ctx, "||",
                                ctx.logicalOr().accept(self), ctx.logicalAnd().accept(self))

    @save_type
    def visitWithCond(self, ctx: MiniDecafParser.WithCondContext):
        return condRule(ctx, ctx.logicalOr().accept(self),
                        ctx.expr().accept(self), ctx.conditional().accept(self))

    @save_type
    def visitWithAsgn(self, ctx: MiniDecafParser.WithAsgnContext):
        res = self.checkBinary(ctx.asgnOp(), ctx.asgnOp().getText(),
                               ctx.unary().accept(self), ctx.assignment().accept(self))
        self.locate(ctx.unary())
        return res

    @save_type
    def visitPostfixCall(self, ctx: MiniDecafParser.PostfixCallContext):
        argTy = self._argTy(ctx.argList())
        func = ctx.Ident().getText()
        rule = self.typeInfo.funcs[func].call()
        return rule(ctx, argTy)

    @save_type
    def visitPostfixArray(self, ctx: MiniDecafParser.PostfixArrayContext):
        return arrayRule(ctx,
                         ctx.postfix().accept(self), ctx.expr().accept(self))

    @save_type
    def visitAtomInteger(self, ctx: MiniDecafParser.AtomIntegerContext):
        if literal_eval(ctx.getText()) == 0:
            return ZeroType()
        else:
            return IntType()

    @save_type
    def visitAtomIdent(self, ctx: MiniDecafParser.AtomIdentContext):
        var = self._var(ctx.Ident())
        return self.var2type[var]

    def visitDeclaration(self, ctx: MiniDecafParser.DeclarationContext):
        var = self._var(ctx.Ident())
        ty = self._declTyp(ctx)
        self.var2type[var] = ty
        if ctx.expr() is not None:
            initTyp = ctx.expr().accept(self)
            asgnRule(ctx, ty, initTyp)

    def checkFunc(self, ctx, isMain=False):
        funcTypeInfo = self._funcTypeInfo(ctx)
        if isMain:
            func = 'main'
        else:
            func = ctx.Ident().getText()
        if func in self.typeInfo.funcs:
            prevFuncTypeInfo = self.typeInfo.funcs[func]
            if not funcTypeInfo.compatible(prevFuncTypeInfo):
                raise Exception(ctx, f"conflicting types for {func}")
        else:
            self.typeInfo.funcs[func] = funcTypeInfo

    def visitFuncDef(self, ctx: MiniDecafParser.FuncDefContext):
        func = ctx.Ident().getText()
        self.curFunc = func
        self.checkFunc(ctx)
        self.visitChildren(ctx)
        self.curFunc = None

    def visitMainFunc(self, ctx: MiniDecafParser.MainFuncContext):
        self.curFunc = 'main'
        self.checkFunc(ctx, True)
        self.visitChildren(ctx)
        self.curFunc = None

    def visitFuncDecl(self, ctx: MiniDecafParser.FuncDeclContext):
        func = ctx.Ident().getText()
        self.curFunc = func
        self.checkFunc(ctx)
        self.curFunc = None

    def paramTy(self, ctx: MiniDecafParser.ParamListContext):
        res = []
        for decl in ctx.declaration():
            if decl.expr() is not None:
                raise Exception(decl, "parameter cannot have initializers")
            paramTy = self._declTyp(decl)
            if isinstance(paramTy, ArrayType):
                raise Exception(decl, "parameter cannot have array types")
            res += [paramTy]
        return res

    def visitDeclExternalDecl(self, ctx: MiniDecafParser.DeclExternalDeclContext):
        ctx = ctx.declaration()
        var = self.nameInfo.globs[ctx.Ident().getText()].var
        ty = self._declTyp(ctx)
        if var in self.var2type:
            prevTy = self.var2type[var]
            if prevTy != ty:
                raise Exception(ctx, f"conflicting types for {var.ident}")
        else:
            self.var2type[var] = ty
        if ctx.expr() is not None:
            initTyp = ctx.expr().accept(self)
            asgnRule(ctx, ty, initTyp)

    def visitReturnStmt(self, ctx: MiniDecafParser.ReturnStmtContext):
        funcRetTy = self.typeInfo.funcs[self.curFunc].retTy
        ty = ctx.expr().accept(self)
        retRule(ctx, funcRetTy, ty)

    def visitIfStmt(self, ctx: MiniDecafParser.IfStmtContext):
        self.visitChildren(ctx)
        stmtCondRule(ctx, ctx.expr().accept(self))  # idempotent

    def visitForDeclStmt(self, ctx: MiniDecafParser.ForDeclStmtContext):
        self.visitChildren(ctx)
        if ctx.ctrl is not None: stmtCondRule(ctx, ctx.ctrl.accept(self))

    def visitForStmt(self, ctx: MiniDecafParser.ForStmtContext):
        self.visitChildren(ctx)
        if ctx.ctrl is not None: stmtCondRule(ctx, ctx.ctrl.accept(self))

    def visitWhileStmt(self, ctx: MiniDecafParser.WhileStmtContext):
        self.visitChildren(ctx)
        stmtCondRule(ctx, ctx.expr().accept(self))

    def visitDoWhileStmt(self, ctx: MiniDecafParser.DoWhileStmtContext):
        self.visitChildren(ctx)
        stmtCondRule(ctx, ctx.expr().accept(self))


class Locator(MiniDecafVisitor):
    """
    visitor mode locating
    """
    def __init__(self, nameInfo, typeInfo: TypeInfo):
        self.nameInfo = nameInfo
        self.typeInfo = typeInfo

    def locate(self, func: str, ctx):
        self.func = func
        res = ctx.accept(self)
        self.func = None
        return res

    def visitAtomIdent(self, ctx: MiniDecafParser.AtomIdentContext):
        var = self.nameInfo[ctx.Ident()]
        if var.offset is None:
            return [GlobalSymbol(var.name)]
        else:
            return [FrameSlot(var.offset)]

    def visitCUnary(self, ctx: MiniDecafParser.CUnaryContext):
        op = ctx.unaryOp().getText()
        if op == '*':
            return [ctx.cast()]

    def visitPostfixArray(self, ctx: MiniDecafParser.PostfixArrayContext):
        fixupMult = self.typeInfo[ctx.postfix()].base.sizeof()
        return [ctx.postfix(), ctx.expr(), Const(fixupMult), Binary('*'), Binary('+')]

    def visitAtomParen(self, ctx: MiniDecafParser.AtomParenContext):
        return ctx.expr().accept(self)


def expandIterableKey(d: list):
    d2 = {}
    for (keys, val) in d:
        for key in keys:
            d2[key] = val
    return d2
