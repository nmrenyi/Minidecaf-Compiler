from minidecaf.IRStr import BaseIRStr
from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser

from minidecaf.types import *
from minidecaf.IRStr import *
from ast import literal_eval

class TypeInfo:
    def __init__(self):
        self.loc = {} # ExprContext -> (IRInstr|ExprContext)+
        self.funcs = {} # str -> FuncTypeInfo
        self._t = {} # ExprContext -> Type

    def lvalueLoc(self, ctx):
        return self.loc[ctx]

    def setLvalueLoc(self, ctx, loc:list):
        self.loc[ctx] = loc

    def __str__(self):
        res = "Lvalue analysis result: (location of expr at lhs == value of rhs):\n\t"
        def p(c):
            return f"{c.start.line},{c.start.column}~{c.stop.line},{c.stop.column}"
        def g(locStep):
            if isinstance(locStep, BaseIRStr):
                return f"{locStep}"
            else:
                return f"[{p(locStep)}]"
        def f(cl):
            ctx, loc = cl
            ctxStr = f"{p(ctx)}"
            locStr = " :: ".join(map(g, loc))
            return f"{ctxStr:>32} : {locStr}"
        res += "\n\t".join(map(f, self.loc.items()))
        res += "\n\nType info for funcs:\n\t"
        def f(nf):
            name, funcInfo = nf
            return f"{name:>32} : ({funcInfo.paramTy}) -> {funcInfo.retTy}"
        res += "\n\t".join(map(f, self.funcs.items()))
        return res

    def __getitem__(self, ctx):
        return self._t[ctx]


class FuncTypeInfo:
    def __init__(self, retTy:Type, paramTy:list):
        self.retTy = retTy
        self.paramTy = paramTy

    def compatible(self, other):
        return self.retTy == other.retTy and self.paramTy == other.paramTy

    def call(self):
        @TypeRule
        def callRule(ctx, argTy:list):
            if self.paramTy == argTy:
                return self.retTy
            return f"bad argument types"
        return callRule


def SaveType(f):
    def g(self, ctx):
        ty = f(self, ctx)
        self.typeInfo._t[ctx] = ty
        return ty
    return g


class Typer(MiniDecafVisitor):
    """
    Type checking.
    Run after name resolution, type checking computes the type of each
    expression, and also check for incompatibilities like int*+int*. Besides
    type checking, Typer also does lvalue analysis i.e. determine which
    expressions are lvalues and their address.
    """
    def __init__(self, nameInfo):
        self.vartyp = {} # Variable -> Type
        self.nameInfo = nameInfo
        self.curFunc = None
        self.typeInfo = TypeInfo()
        self.locator = Locator(self.nameInfo, self.typeInfo)

    def visitChildren(self, ctx):
        ty = MiniDecafVisitor.visitChildren(self, ctx)
        self.typeInfo._t[ctx] = ty
        return ty

    def _var(self, term):
        return self.nameInfo[term]

    def _declTyp(self, ctx:MiniDecafParser.DeclarationContext):
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

    def _argTy(self, ctx:MiniDecafParser.ArgListContext):
        return list(map(lambda x: x.accept(self), ctx.expr()))

    def visitPtrType(self, ctx:MiniDecafParser.PtrTypeContext):
        return PtrType(ctx.ty().accept(self))

    def visitIntType(self, ctx:MiniDecafParser.IntTypeContext):
        return IntType()

    def locate(self, ctx):
        loc = self.locator.locate(self.curFunc, ctx)
        if loc is None:
            raise Exception(ctx, "lvalue expected")
        self.typeInfo.setLvalueLoc(ctx, loc)

    def checkUnary(self, ctx, op:str, ty:Type):
        rule = expandIterableKey([
            (['-', '!', '~'],   intUnaopRule),
            (['&'],             addrofRule),
            (['*'],             derefRule),
        ])[op]
        return rule(ctx, ty)

    def checkBinary(self, ctx, op:str, lhs:Type, rhs:Type):
        rule = expandIterableKey([
            (['*', '/', '%'] + ["&&", "||"],    intBinopRule),
            (["==", "!="],                         eqRule),
            (["<", "<=", ">", ">="],               relRule),
            (['='],                         asgnRule),
            (['+'],                         tryEach('+', intBinopRule, ptrArithRule)),
            (['-'],                         tryEach('-', intBinopRule, ptrArithRule, ptrDiffRule)),
        ])[op]
        return rule(ctx, lhs, rhs)

    @SaveType
    def visitCCast(self, ctx:MiniDecafParser.CCastContext):
        ctx.cast().accept(self)
        return ctx.ty().accept(self)

    @SaveType
    def visitCUnary(self, ctx:MiniDecafParser.CUnaryContext):
        res = self.checkUnary(ctx.unaryOp(), ctx.unaryOp().getText(),
                ctx.cast().accept(self))
        if ctx.unaryOp().getText() == '&':
            self.locate(ctx.cast())
        return res

    @SaveType
    def visitAtomParen(self, ctx:MiniDecafParser.AtomParenContext):
        return ctx.expr().accept(self)

    @SaveType
    def visitCAdd(self, ctx:MiniDecafParser.CAddContext):
        return self.checkBinary(ctx.addOp(), ctx.addOp().getText(),
                ctx.add().accept(self), ctx.mul().accept(self))

    @SaveType
    def visitCMul(self, ctx:MiniDecafParser.CMulContext):
        return self.checkBinary(ctx.mulOp(), ctx.mulOp().getText(),
                ctx.mul().accept(self), ctx.cast().accept(self))

    @SaveType
    def visitCRel(self, ctx:MiniDecafParser.CRelContext):
        return self.checkBinary(ctx.relOp(), ctx.relOp().getText(),
                ctx.rel().accept(self), ctx.add().accept(self))

    @SaveType
    def visitCEq(self, ctx:MiniDecafParser.CEqContext):
        return self.checkBinary(ctx.eqOp(), ctx.eqOp().getText(),
                ctx.eq().accept(self), ctx.rel().accept(self))

    @SaveType
    def visitCLand(self, ctx:MiniDecafParser.CLandContext):
        return self.checkBinary(ctx, "&&",
                ctx.land().accept(self), ctx.eq().accept(self))

    @SaveType
    def visitCLor(self, ctx:MiniDecafParser.CLorContext):
        return self.checkBinary(ctx, "||",
                ctx.lor().accept(self), ctx.land().accept(self))

    @SaveType
    def visitWithCond(self, ctx:MiniDecafParser.WithCondContext):
        return condRule(ctx, ctx.lor().accept(self),
                ctx.expr().accept(self), ctx.cond().accept(self))

    @SaveType
    def visitWithAsgn(self, ctx:MiniDecafParser.WithAsgnContext):
        res = self.checkBinary(ctx.asgnOp(), ctx.asgnOp().getText(),
                ctx.unary().accept(self), ctx.asgn().accept(self))
        self.locate(ctx.unary())
        return res

    @SaveType
    def visitPostfixCall(self, ctx:MiniDecafParser.PostfixCallContext):
        argTy = self._argTy(ctx.argList())
        func = ctx.Ident().getText()
        rule = self.typeInfo.funcs[func].call()
        return rule(ctx, argTy)

    @SaveType
    def visitPostfixArray(self, ctx:MiniDecafParser.PostfixArrayContext):
        return arrayRule(ctx,
                ctx.postfix().accept(self), ctx.expr().accept(self))

    @SaveType
    def visitAtomInteger(self, ctx:MiniDecafParser.AtomIntegerContext):
        if literal_eval(ctx.getText()) == 0:
            return ZeroType()
        else:
            return IntType()

    @SaveType
    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        var = self._var(ctx.Ident())
        return self.vartyp[var]

    def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
        var = self._var(ctx.Ident())
        ty = self._declTyp(ctx)
        self.vartyp[var] = ty
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

    def visitFuncDef(self, ctx:MiniDecafParser.FuncDefContext):
        func = ctx.Ident().getText()
        self.curFunc = func
        self.checkFunc(ctx)
        self.visitChildren(ctx)
        self.curFunc = None

    def visitMainFunc(self, ctx:MiniDecafParser.MainFuncContext):
        self.curFunc = 'main'
        self.checkFunc(ctx, True)
        self.visitChildren(ctx)
        self.curFunc = None

    def visitFuncDecl(self, ctx:MiniDecafParser.FuncDeclContext):
        func = ctx.Ident().getText()
        self.curFunc = func
        self.checkFunc(ctx)
        self.curFunc = None

    def paramTy(self, ctx:MiniDecafParser.ParamListContext):
        res = []
        for decl in ctx.declaration():
            if decl.expr() is not None:
                raise Exception(decl, "parameter cannot have initializers")
            paramTy = self._declTyp(decl)
            if isinstance(paramTy, ArrayType):
                raise Exception(decl, "parameter cannot have array types")
            res += [paramTy]
        return res

    def visitDeclExternalDecl(self, ctx:MiniDecafParser.DeclExternalDeclContext):
        ctx = ctx.decl()
        var = self.nameInfo.globs[ctx.Ident().getText()].var
        ty = self._declTyp(ctx)
        if var in self.vartyp:
            prevTy = self.vartyp[var]
            if prevTy != ty:
                raise Exception(ctx, f"conflicting types for {var.ident}")
        else:
            self.vartyp[var] = ty
        if ctx.expr() is not None:
            initTyp = ctx.expr().accept(self)
            asgnRule(ctx, ty, initTyp)

    def visitReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        funcRetTy = self.typeInfo.funcs[self.curFunc].retTy
        ty = ctx.expr().accept(self)
        retRule(ctx, funcRetTy, ty)

    def visitIfStmt(self, ctx:MiniDecafParser.IfStmtContext):
        self.visitChildren(ctx)
        stmtCondRule(ctx, ctx.expr().accept(self)) # idempotent

    def visitForDeclStmt(self, ctx:MiniDecafParser.ForDeclStmtContext):
        self.visitChildren(ctx)
        if ctx.ctrl is not None: stmtCondRule(ctx, ctx.ctrl.accept(self))

    def visitForStmt(self, ctx:MiniDecafParser.ForStmtContext):
        self.visitChildren(ctx)
        if ctx.ctrl is not None: stmtCondRule(ctx, ctx.ctrl.accept(self))

    def visitWhileStmt(self, ctx:MiniDecafParser.WhileStmtContext):
        self.visitChildren(ctx)
        stmtCondRule(ctx, ctx.expr().accept(self))

    def visitDoWhileStmt(self, ctx:MiniDecafParser.DoWhileStmtContext):
        self.visitChildren(ctx)
        stmtCondRule(ctx, ctx.expr().accept(self))


class Locator(MiniDecafVisitor):
    def __init__(self, nameInfo, typeInfo:TypeInfo):
        self.nameInfo = nameInfo
        self.typeInfo = typeInfo

    def locate(self, func:str, ctx):
        self.func = func
        res = ctx.accept(self)
        self.func = None
        return res

    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        var = self.nameInfo[ctx.Ident()]
        if var.offset is None:
            return [GlobalSymbol(var.ident)]
        else:
            return [FrameSlot(var.offset)]

    def visitCUnary(self, ctx:MiniDecafParser.CUnaryContext):
        op = ctx.unaryOp().getText()
        if op == '*':
            return [ctx.cast()]

    def visitPostfixArray(self, ctx:MiniDecafParser.PostfixArrayContext):
        fixupMult = self.typeInfo[ctx.postfix()].base.sizeof()
        return [ctx.postfix(), ctx.expr(), Const(fixupMult), Binary('*'), Binary('+')]

    def visitAtomParen(self, ctx:MiniDecafParser.AtomParenContext):
        return ctx.expr().accept(self)

def expandIterableKey(d:list):
    d2 = {}
    for (keys, val) in d:
        for key in keys:
            d2[key] = val
    return d2
