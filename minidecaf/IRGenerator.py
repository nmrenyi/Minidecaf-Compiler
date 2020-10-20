import minidecaf.IRStr as IRStr
from .IRStr import Unary, Binary, Const, BaseIRStr
from .NameParser import Variable
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor
from .types import ArrayType, PtrType


class IRGenerator(MiniDecafVisitor):
    """
    A visitor for going through the whole ast, inherited from MiniDecafVisitor
    The accept method in different node uses the vistor's different methods, that is the visitor pattern.
    """

    def __init__(self, ir_container, name_manager, type_info):
        self._container = ir_container
        self.labelManager = LabelManager()
        self.nameManager = name_manager
        self._curFuncNameInfo = None
        self.typeInfo = type_info

    def _var(self, term):
        return self._curFuncNameInfo[term]

    def emit_var(self, var: Variable):
        if var.offset is None:
            self._container.add(IRStr.GlobalSymbol(var.name))
        else:
            self._container.add(IRStr.FrameSlot(var.offset))

    def get_position(self, term):
        '''
        return the position relative to fp for specific term
        '''
        return self._curFuncNameInfo[term].offset
        # return self.nameManager[term].offset

    def get_ident(self, term):
        return self._curFuncNameInfo[term].name

    def loop(self, name, init, cond, body, post):
        '''
        general loop structure
        '''
        entry_label = self.labelManager.new_label(f"{name}_entry")
        if post is not None:  # have statement like incrementation
            continue_label = self.labelManager.new_label(f"{name}_continue")
        else:
            continue_label = entry_label  # go to start directly
        exit_label = self.labelManager.new_label(f"{name}_exit")

        self.labelManager.enter_loop(continue_label, exit_label)
        if init is not None:
            init.accept(self)
            if isinstance(init, MiniDecafParser.ExprContext):
                self._container.add(IRStr.Pop())
        self._container.add(IRStr.Label(entry_label))
        if cond is not None:
            cond.accept(self)  # check loop condition
        else:
            self._container.add(IRStr.Const(1))  # loop forever
        self._container.add(IRStr.Branch("beqz", exit_label))  # if cond is not satisfied (stack top == 0), then exit
        body.accept(self)  # calculate body part

        if post is not None:
            self._container.add(IRStr.Label(continue_label))  # go to post
            post.accept(self)  # calculate post
            if isinstance(post, MiniDecafParser.ExprContext):
                self._container.add(IRStr.Pop())

        self._container.add(IRStr.Branch("br", entry_label))  # go to entry, loop!
        self._container.add(IRStr.Label(exit_label))  # exit label

        self.labelManager.exit_loop()

    def visitForDeclStmt(self, ctx: MiniDecafParser.ForDeclStmtContext):
        self.loop("for", ctx.init, ctx.ctrl, ctx.stmt(), ctx.post)
        self._container.add_list([IRStr.Pop()] * self._curFuncNameInfo.blockSlots[ctx])

    def visitForStmt(self, ctx: MiniDecafParser.ForStmtContext):
        self.loop("for", ctx.init, ctx.ctrl, ctx.stmt(), ctx.post)

    def visitWhileStmt(self, ctx: MiniDecafParser.WhileStmtContext):
        self.loop("while", None, ctx.expr(), ctx.stmt(), None)

    def visitDoWhileStmt(self, ctx: MiniDecafParser.DoWhileStmtContext):
        self.loop("dowhile", ctx.stmt(), ctx.expr(), ctx.stmt(), None)

    def visitBreakStmt(self, ctx: MiniDecafParser.BreakStmtContext):
        self._container.add(IRStr.Branch("br", self.labelManager.break_label()))

    def visitContinueStmt(self, ctx: MiniDecafParser.ContinueStmtContext):
        self._container.add(IRStr.Branch("br", self.labelManager.continue_label()))

    def visitReturnStmt(self, ctx: MiniDecafParser.ReturnStmtContext):
        self.visitChildren(ctx)
        self._container.add(IRStr.Ret())

    def visitExprStmt(self, ctx: MiniDecafParser.ExprStmtContext):
        self.visitChildren(ctx)
        if ctx.expr() is not None:
            # empty expression shouldn't be popped (step 8 empty expr won't pass without this)
            # non-empty expression should be popped (int i = 0; i = 3; see the ir output)
            self._container.add(IRStr.Pop())

    def visitExpr(self, ctx: MiniDecafParser.ExprContext):
        self.visitChildren(ctx)

    def visitDeclaration(self, ctx: MiniDecafParser.DeclarationContext):
        var = self.nameManager.term2Var[ctx.Ident()]
        if ctx.expr() is not None:
            ctx.expr().accept(self)
        else:
            self._container.add_list([Const(0)] * (var.size // 4))

    def visitDeclExternalDecl(self, ctx: MiniDecafParser.DeclExternalDeclContext):
        pass

    def visitCompound(self, ctx: MiniDecafParser.CompoundContext):
        """
        visit block here
        pop the variables defined in the block
        """
        self.visitChildren(ctx)
        self._container.add_list([IRStr.Pop()] * self._curFuncNameInfo.blockSlots[ctx])

    def _compute_addr(self, lvalue: Unary):
        if isinstance(lvalue, MiniDecafParser.TUnaryContext):
            return self._compute_addr(lvalue.postfix())
        if isinstance(lvalue, MiniDecafParser.PostfixContext):
            return self._compute_addr(lvalue.atom())
        if isinstance(lvalue, MiniDecafParser.AtomIdentContext):
            var = self._var(lvalue.Ident())
            return self.emit_var(var)
        elif isinstance(lvalue, MiniDecafParser.AtomParenContext):
            return self._compute_addr(lvalue.expr())
        raise Exception(f"{lvalue.getText()} is not a lvalue")

    def visitWithAsgn(self, ctx: MiniDecafParser.WithAsgnContext):
        ctx.assignment().accept(self)
        # self._computeAddr(ctx.unary())
        self.emit_loc(ctx.unary())
        self._container.add(IRStr.Store())

    def visitIfStmt(self, ctx: MiniDecafParser.IfStmtContext):
        """
        Referenced to TA implementation
        """
        ctx.expr().accept(self)  # calculate condition first
        end_label = self.labelManager.new_label("if_end")
        else_label = self.labelManager.new_label("if_else")
        if ctx.el is not None:
            self._container.add(IRStr.Branch("beqz", else_label))
            ctx.th.accept(self)
            self._container.add_list([IRStr.Branch("br", end_label), IRStr.Label(else_label)])
            ctx.el.accept(self)
            self._container.add(IRStr.Label(end_label))
        else:  # no else statement here
            self._container.add(IRStr.Branch("beqz", end_label))
            ctx.th.accept(self)
            self._container.add(IRStr.Label(end_label))

    def visitWithCond(self, ctx: MiniDecafParser.WithCondContext):
        """
        Reference to TA implementation
        """
        ctx.logicalOr().accept(self)  # calc CLor first
        exit_label = self.labelManager.new_label("cond_end")
        else_label = self.labelManager.new_label("cond_else")
        self._container.add(IRStr.Branch("beqz", else_label))  # if false, go to else
        ctx.expr().accept(self)  # if true, do expr
        self._container.add_list([IRStr.Branch("br", exit_label), IRStr.Label(else_label)])
        ctx.conditional().accept(self)
        self._container.add(IRStr.Label(exit_label))

    def visitAtomIdent(self, ctx: MiniDecafParser.AtomIdentContext):
        offset = self.get_position(ctx.Ident())
        if offset is None:
            self._container.add(IRStr.GlobalSymbol(self.get_ident(ctx.Ident())))
        else:
            self._container.add(IRStr.FrameSlot(offset))  # get position from nameManager
        if not isinstance(self.typeInfo[ctx], ArrayType):
            self._container.add(IRStr.Load())

    def visitCUnary(self, ctx: MiniDecafParser.CUnaryContext):
        if ctx.unaryOp() is not None:
            op = ctx.unaryOp().getText()
            if op == '&':
                self.emit_loc(ctx.cast())
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

    def visitAtomInteger(self, ctx: MiniDecafParser.AtomIntegerContext):
        # no children in atomInteger branch, get the Integer DIRECTLY
        if ctx.Integer() is not None:
            v = int(ctx.Integer().getText())
            self._container.add(IRStr.Const(v))

    # def visitCAdd(self, ctx:MiniDecafParser.CAddContext):
    #     self.visitChildren(ctx)
    #     if ctx.addOp() is not None:
    #         self._container.add(IRStr.Binary(ctx.addOp().getText()))

    def visitCAdd(self, ctx: MiniDecafParser.CAddContext):
        if ctx.addOp() is not None:
            self._add_expr(ctx, ctx.addOp().getText(), ctx.additive(), ctx.multiplicative())

    def visitCMul(self, ctx: MiniDecafParser.CMulContext):
        self.visitChildren(ctx)
        if ctx.mulOp() is not None:
            self._container.add(IRStr.Binary(ctx.mulOp().getText()))

    def visitCLand(self, ctx: MiniDecafParser.CLandContext):
        self.visitChildren(ctx)
        if ctx.andOp() is not None:
            self._container.add(IRStr.Binary(ctx.andOp().getText()))

    def visitCLor(self, ctx: MiniDecafParser.CLorContext):
        self.visitChildren(ctx)
        if ctx.orOp() is not None:
            self._container.add(IRStr.Binary(ctx.orOp().getText()))

    def visitCRel(self, ctx: MiniDecafParser.CRelContext):
        self.visitChildren(ctx)
        if ctx.relOp() is not None:
            self._container.add(IRStr.Binary(ctx.relOp().getText()))

    def visitCEq(self, ctx: MiniDecafParser.CEqContext):
        self.visitChildren(ctx)
        if ctx.eqOp() is not None:
            self._container.add(IRStr.Binary(ctx.eqOp().getText()))

    def visitFuncDef(self, ctx: MiniDecafParser.FuncDefContext):
        if ctx.Ident() is not None:
            func = ctx.Ident().getText()
            self._curFuncNameInfo = self.nameManager.nameManager[func]

            # nParams = len(self.typeInfo.funcs[func].paramTy)
            param_info = self.nameManager.paramInfos[func]

            self._container.enter_function(func, param_info)
            ctx.compound().accept(self)
            self._container.exit_function()

    def visitMainFunc(self, ctx: MiniDecafParser.MainFuncContext):
        func = 'main'
        self._curFuncNameInfo = self.nameManager.nameManager[func]
        param_info = self.nameManager.paramInfos[func]
        self._container.enter_function(func, param_info)
        ctx.compound().accept(self)
        self._container.exit_function()

    def visitFuncDecl(self, ctx: MiniDecafParser.FuncDeclContext):
        # self.visitChildren(ctx)
        if ctx.Ident() is not None:
            self._container.add_func_decl(ctx.Ident().getText())

    def visitPostfixCall(self, ctx: MiniDecafParser.PostfixContext):
        args = ctx.argList().expr()
        arg_cnt = 0
        for arg in reversed(args):  # push into stack in a reversed way
            arg.accept(self)
            arg_cnt += 1

        call_func_param_num = self.nameManager.paramInfos[ctx.Ident().getText()].paramNum
        assert arg_cnt == call_func_param_num
        if ctx.Ident() is not None:
            func = ctx.Ident().getText()
            self._container.add(IRStr.Call(func, self.nameManager.paramInfos[func].paramNum))

    def visitProg(self, ctx: MiniDecafParser.ProgContext):
        for globInfo in self.nameManager.globInfos.values():
            self._container.add_global(globInfo)
        self.visitChildren(ctx)

    def _add_expr(self, ctx, op, lhs, rhs):
        if isinstance(self.typeInfo[lhs], PtrType):
            sz = self.typeInfo[lhs].sizeof()
            if isinstance(self.typeInfo[rhs], PtrType):  # ptr - ptr
                lhs.accept(self)
                rhs.accept(self)
                self._container.add_list([Binary(op)])
                self._container.add_list([Const(sz), Binary('/')])
            else:  # ptr +- int
                lhs.accept(self)
                rhs.accept(self)
                self._container.add_list([Const(sz), Binary('*')])
                self._container.add_list([Binary(op)])
        else:
            sz = self.typeInfo[rhs].sizeof()
            if isinstance(self.typeInfo[rhs], PtrType):  # int +- ptr
                lhs.accept(self)
                self._container.add_list([Const(sz), Binary('*')])
                rhs.accept(self)
                self._container.add_list([Binary(op)])
            else:  # int +- int
                self.visitChildren(ctx)
                self._container.add_list([Binary(op)])

    def emit_loc(self, lvalue: MiniDecafParser.ExprContext):
        loc = self.typeInfo.lvalueLoc(lvalue)
        for locStep in loc:
            if isinstance(locStep, BaseIRStr):
                self._container.add_list([locStep])
            else:
                locStep.accept(self)

    def visitPostfixArray(self, ctx: MiniDecafParser.PostfixArrayContext):
        fixup_mult = self.typeInfo[ctx.postfix()].base.sizeof()
        ctx.postfix().accept(self)
        ctx.expr().accept(self)
        self._container.add_list([Const(fixup_mult), Binary('*'), Binary('+')])
        if not isinstance(self.typeInfo[ctx], ArrayType):
            self._container.add_list([IRStr.Load()])


class LabelManager:
    """
    Label Manager
    Counter for labels in case of duplication
    Referenced to TA's implementation
    """

    def __init__(self):
        self._labels = {}
        self.loopEntry = []  # labels for loop entry
        self.loopExit = []  # labels for loop exit

    def new_label(self, scope="_L"):
        if scope not in self._labels:
            self._labels[scope] = 1
        else:
            self._labels[scope] += 1
        return f"{scope}_{self._labels[scope]}"

    def enter_loop(self, entry_label, exit_label):
        """
        add loop entry control
        append entry and exit label to corresponding list
        """
        self.loopEntry.append(entry_label)
        self.loopExit.append(exit_label)

    def exit_loop(self):
        """
        add loop exit control
        pop loop entry/exit label
        """
        self.loopEntry.pop()
        self.loopExit.pop()

    def break_label(self):
        """
        return the last break label
        if no break label exists, the 'break' must be outside a loop
        """
        if len(self.loopExit) == 0:
            raise Exception("break not in a loop")
        return self.loopExit[-1]

    def continue_label(self):
        """
        return the last continue label
        if no continue label exists, the 'continue' must be outside a loop

        """
        if len(self.loopExit) == 0:
            raise Exception("continue not in a loop")
        return self.loopEntry[-1]
