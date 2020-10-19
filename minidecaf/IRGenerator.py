from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
import minidecaf.IRStr as IRStr
from .NameParser import Variable
from .IRStr import Unary, Binary, Const, BaseIRStr
from .types import ArrayType, PtrType

class IRGenerator(MiniDecafVisitor):
    '''
    A visitor for going through the whole ast, inherited from MiniDecafVisitor
    The accept method in different node uses the vistor's different methods, that is the visitor pattern.
    '''
    def __init__(self, irContainer, nameManager, typeInfo):
        self._container = irContainer
        self.labelManager = LabelManager()
        self.nameManager = nameManager
        self._curFuncNameInfo = None
        self.typeInfo = typeInfo

    def _var(self, term):
        return self._curFuncNameInfo[term]

    def emitVar(self, var:Variable):
        if var.offset is None:
            self._container.add(IRStr.GlobalSymbol(var.name))
        else:
            self._container.add(IRStr.FrameSlot(var.offset))

    def getPosition(self, term):
        '''
        return the position relative to fp for specific term
        '''
        return self._curFuncNameInfo[term].offset
        # return self.nameManager[term].offset
    def getIdent(self, term):
        return self._curFuncNameInfo[term].name

    def loop(self, name, init, cond, body, post):
        '''
        general loop structure
        '''
        entryLabel = self.labelManager.newLabel(f"{name}_entry")
        if post is not None: # have statement like incrementation
            continueLabel = self.labelManager.newLabel(f"{name}_continue")
        else:
            continueLabel = entryLabel # go to start directly
        exitLabel = self.labelManager.newLabel(f"{name}_exit")

        self.labelManager.enterLoop(continueLabel, exitLabel)
        if init is not None:
            init.accept(self)
            if isinstance(init, MiniDecafParser.ExprContext):
                self._container.add(IRStr.Pop())
        self._container.add(IRStr.Label(entryLabel))
        if cond is not None:
            cond.accept(self) # check loop condition
        else:
            self._container.add(IRStr.Const(1)) # loop forever
        self._container.add(IRStr.Branch("beqz", exitLabel)) # if cond is not satisfied (stack top == 0), then exit
        body.accept(self) # calculate body part

        if post is not None:
            self._container.add(IRStr.Label(continueLabel)) # go to post
            post.accept(self) # calculate post
            if isinstance(post, MiniDecafParser.ExprContext):
                self._container.add(IRStr.Pop())

        self._container.add(IRStr.Branch("br", entryLabel)) # go to entry, loop!
        self._container.add(IRStr.Label(exitLabel)) # exit label

        self.labelManager.exitLoop()

    def visitForDeclStmt(self, ctx:MiniDecafParser.ForDeclStmtContext):
        self.loop("for", ctx.init, ctx.ctrl, ctx.stmt(), ctx.post)
        self._container.addList([IRStr.Pop()] * self._curFuncNameInfo.blockSlots[ctx])

    def visitForStmt(self, ctx:MiniDecafParser.ForStmtContext):
        self.loop("for", ctx.init, ctx.ctrl, ctx.stmt(), ctx.post)

    def visitWhileStmt(self, ctx:MiniDecafParser.WhileStmtContext):
        self.loop("while", None, ctx.expr(), ctx.stmt(), None)

    def visitDoWhileStmt(self, ctx:MiniDecafParser.DoWhileStmtContext):
        self.loop("dowhile", ctx.stmt(), ctx.expr(), ctx.stmt(), None)
    
    def visitBreakStmt(self, ctx:MiniDecafParser.BreakStmtContext):
        self._container.add(IRStr.Branch("br", self.labelManager.breakLabel()))

    def visitContinueStmt(self, ctx:MiniDecafParser.ContinueStmtContext):
        self._container.add(IRStr.Branch("br", self.labelManager.continueLabel()))

    def visitReturnStmt(self, ctx:MiniDecafParser.ReturnStmtContext):
        self.visitChildren(ctx)
        self._container.add(IRStr.Ret())

    def visitExprStmt(self, ctx:MiniDecafParser.ExprStmtContext):
        self.visitChildren(ctx)
        if ctx.expr() is not None: 
            # empty expression shouldn't be popped (step 8 empty expr won't pass without this)
            # non-empty expression should be popped (int i = 0; i = 3; see the ir output)
            self._container.add(IRStr.Pop())

    def visitExpr(self, ctx:MiniDecafParser.ExprContext):
        self.visitChildren(ctx)

    # def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
    #     if ctx.Ident() is not None:
    #         var = ctx.Ident().getText()
    #         if ctx.expr() is not None:
    #             ctx.expr().accept(self) # get expression value
    #         else:
    #             self._container.add(IRStr.Const(0)) # default value is zero

    def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
        var = self.nameManager[ctx.Ident()]
        if ctx.expr() is not None:
            ctx.expr().accept(self)
        else:
            self._container.addList([Const(0)] * (var.size//4))

    def visitCompound(self, ctx:MiniDecafParser.CompoundContext):
        '''
        visit block here
        pop the variables defined in the block
        '''
        self.visitChildren(ctx)
        self._container.addList([IRStr.Pop()] * self._curFuncNameInfo.blockSlots[ctx])

    def _computeAddr(self, lvalue:Unary):
        if isinstance(lvalue, MiniDecafParser.TUnaryContext):
            return self._computeAddr(lvalue.postfix())
        if isinstance(lvalue, MiniDecafParser.PostfixContext):
            return self._computeAddr(lvalue.atom())
        if isinstance(lvalue, MiniDecafParser.AtomIdentContext):
            var = self._var(lvalue.Ident())
            return self.emitVar(var)
        elif isinstance(lvalue, MiniDecafParser.AtomParenContext):
            return self._computeAddr(lvalue.expr())
        raise Exception(f"{lvalue.getText()} is not a lvalue")

    def visitWithAsgn(self, ctx:MiniDecafParser.WithAsgnContext):
        ctx.assignment().accept(self)
        # self._computeAddr(ctx.unary())
        self.emitLoc(ctx.unary())
        self._container.add(IRStr.Store())

    def visitIfStmt(self, ctx:MiniDecafParser.IfStmtContext):
        '''
        Referenced to TA implementation
        '''
        ctx.expr().accept(self) # calculate condition first
        endLabel = self.labelManager.newLabel("if_end")
        elseLabel = self.labelManager.newLabel("if_else")
        if ctx.el is not None:
            self._container.add(IRStr.Branch("beqz", elseLabel))
            ctx.th.accept(self)
            self._container.addList([IRStr.Branch("br", endLabel), IRStr.Label(elseLabel)])
            ctx.el.accept(self)
            self._container.add(IRStr.Label(endLabel))
        else: # no else statement here
            self._container.add(IRStr.Branch("beqz", endLabel))
            ctx.th.accept(self)
            self._container.add(IRStr.Label(endLabel))

    def visitWithCond(self, ctx:MiniDecafParser.WithCondContext):
        '''
        Reference to TA implementation
        '''
        ctx.logicalOr().accept(self) # calc CLor first
        exitLabel = self.labelManager.newLabel("cond_end")
        elseLabel = self.labelManager.newLabel("cond_else")
        self._container.add(IRStr.Branch("beqz", elseLabel)) # if false, go to else
        ctx.expr().accept(self) # if true, do expr
        self._container.addList([IRStr.Branch("br", exitLabel), IRStr.Label(elseLabel)])
        ctx.conditional().accept(self)
        self._container.add(IRStr.Label(exitLabel))

    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        offset = self.getPosition(ctx.Ident())
        if offset is None:
            self._container.add(IRStr.GlobalSymbol(self.getIdent(ctx.Ident())))
        else:
            self._container.add(IRStr.FrameSlot(offset)) # get position from nameManager
        if not isinstance(self.typeInfo[ctx], ArrayType):
            self._container.add(IRStr.Load())

    def visitCUnary(self, ctx:MiniDecafParser.CUnaryContext):
        if ctx.unaryOp() is not None:
            op = ctx.unaryOp().getText()
            if op == '&':
                self.emitLoc(ctx.cast())
            elif op == '*':
                self.visitChildren(ctx)
                self._container.add(IRStr.Load())
            else:
                self.visitChildren(ctx)
                self._container.add(Unary(op))

    # def visitCUnary(self, ctx:MiniDecafParser.CUnaryContext):
    #     self.visitChildren(ctx)
    #     if ctx.unaryOp() is not None:
    #         self._container.add(IRStr.Unary(ctx.unaryOp().getText()))
    
    def visitAtomInteger(self, ctx:MiniDecafParser.AtomIntegerContext):
        # no children in atomInteger branch, get the Integer DIRECTLY
        if ctx.Integer() is not None:
            v = int(ctx.Integer().getText())
            self._container.add(IRStr.Const(v))

    # def visitCAdd(self, ctx:MiniDecafParser.CAddContext):
    #     self.visitChildren(ctx)
    #     if ctx.addOp() is not None:
    #         self._container.add(IRStr.Binary(ctx.addOp().getText()))
    
    def visitCAdd(self, ctx:MiniDecafParser.CAddContext):
        if ctx.addOp() is not None:
            self._addExpr(ctx, ctx.addOp().getText(), ctx.additive(), ctx.multiplicative())

    def visitCMul(self, ctx:MiniDecafParser.CMulContext):
        self.visitChildren(ctx)
        if ctx.mulOp() is not None:
            self._container.add(IRStr.Binary(ctx.mulOp().getText()))

    def visitCLand(self, ctx:MiniDecafParser.CLandContext):
        self.visitChildren(ctx)
        if ctx.andOp() is not None:
            self._container.add(IRStr.Binary(ctx.andOp().getText()))

    def visitCLor(self, ctx:MiniDecafParser.CLorContext):
        self.visitChildren(ctx)
        if ctx.orOp() is not None:
            self._container.add(IRStr.Binary(ctx.orOp().getText()))

    def visitCRel(self, ctx:MiniDecafParser.CRelContext):
        self.visitChildren(ctx)
        if ctx.relOp() is not None:
            self._container.add(IRStr.Binary(ctx.relOp().getText()))
    
    def visitCEq(self, ctx:MiniDecafParser.CEqContext):
        self.visitChildren(ctx)
        if ctx.eqOp() is not None:
            self._container.add(IRStr.Binary(ctx.eqOp().getText()))
    
    def visitFuncDef(self, ctx:MiniDecafParser.FuncDefContext):
        if ctx.Ident() is not None:
            func = ctx.Ident().getText()
            self._curFuncNameInfo = self.nameManager.nameManager[func]
            
            # nParams = len(self.typeInfo.funcs[func].paramTy)
            paramInfo = self.nameManager.paramInfos[func]

            self._container.enterFunction(func, paramInfo)
            ctx.compound().accept(self)
            self._container.exitFunction()

    def visitMainFunc(self, ctx:MiniDecafParser.MainFuncContext):
        func = 'main'
        self._curFuncNameInfo = self.nameManager.nameManager[func]
        paramInfo = self.nameManager.paramInfos[func]
        self._container.enterFunction(func, paramInfo)
        ctx.compound().accept(self)
        self._container.exitFunction()

    def visitFuncDecl(self, ctx:MiniDecafParser.FuncDeclContext):
        self.visitChildren(ctx)
        if ctx.Ident() is not None:
            self._container.addFuncDecl(ctx.Ident().getText())

    def visitPostfixCall(self, ctx:MiniDecafParser.PostfixContext):
        args = ctx.argList().expr()
        arg_cnt = 0
        for arg in reversed(args):  # push into stack in a reversed way
            arg.accept(self)
            arg_cnt += 1

        call_func_paramNum = self.nameManager.paramInfos[ctx.Ident().getText()].paramNum
        assert arg_cnt == call_func_paramNum
        if ctx.Ident() is not None:
            func = ctx.Ident().getText()
            self._container.add(IRStr.Call(func, self.nameManager.paramInfos[func].paramNum))

    def visitProg(self, ctx:MiniDecafParser.ProgContext):
        for globInfo in self.nameManager.globInfos.values():
            self._container.addGlobal(globInfo)
        self.visitChildren(ctx)
    def _addExpr(self, ctx, op, lhs, rhs):
        if isinstance(self.typeInfo[lhs], PtrType):
            sz = self.typeInfo[lhs].sizeof()
            if isinstance(self.typeInfo[rhs], PtrType): # ptr - ptr
                lhs.accept(self)
                rhs.accept(self)
                self._container.addList([Binary(op)])
                self._container.addList([Const(sz), Binary('/')])
            else: # ptr +- int
                lhs.accept(self)
                rhs.accept(self)
                self._container.addList([Const(sz), Binary('*')])
                self._container.addList([Binary(op)])
        else:
            sz = self.typeInfo[rhs].sizeof()
            if isinstance(self.typeInfo[rhs], PtrType): # int +- ptr
                lhs.accept(self)
                self._container.addList([Const(sz), Binary('*')])
                rhs.accept(self)
                self._container.addList([Binary(op)])
            else: # int +- int
                self.visitChildren(ctx)
                self._container.addList([Binary(op)])


    def emitLoc(self, lvalue:MiniDecafParser.ExprContext):
        loc = self.typeInfo.lvalueLoc(lvalue)
        for locStep in loc:
            if isinstance(locStep, BaseIRStr):
                self._container.addList([locStep])
            else:
                locStep.accept(self)

    def visitPostfixArray(self, ctx:MiniDecafParser.PostfixArrayContext):
        fixupMult = self.typeInfo[ctx.postfix()].base.sizeof()
        ctx.postfix().accept(self)
        ctx.expr().accept(self)
        self._container.addList([Const(fixupMult), Binary('*'), Binary('+')])
        if not isinstance(self.typeInfo[ctx], ArrayType):
            self._container.addList([IRStr.Load()])


class LabelManager:
    '''
    Label Manager
    Counter for labels in case of duplication
    Referenced to TA's implemenation
    '''
    def __init__(self):
        self._labels = {}
        self.loopEntry = [] # labels for loop entry
        self.loopExit = [] # labels for loop exit

    def newLabel(self, scope="_L"):
        if scope not in self._labels:
            self._labels[scope] = 1
        else:
            self._labels[scope] += 1
        return f"{scope}_{self._labels[scope]}"

    def enterLoop(self, entry, exit):
        '''
        add loop entry control
        append entry and exit label to corresponding list
        '''
        self.loopEntry.append(entry)
        self.loopExit.append(exit)

    def exitLoop(self):
        '''
        add loop exit control
        pop loop entry/exit label
        '''
        self.loopEntry.pop()
        self.loopExit.pop()

    def breakLabel(self):
        '''
        return the last break label
        if no break label exists, the 'break' must be outside a loop
        '''
        if len(self.loopExit) == 0:
            raise Exception("break not in a loop")
        return self.loopExit[-1]

    def continueLabel(self):
        '''
        return the last continue label
        if no continue label exists, the 'continue' must be outside a loop

        '''
        if len(self.loopExit) == 0:
            raise Exception("continue not in a loop")
        return self.loopEntry[-1]

