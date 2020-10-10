from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
import minidecaf.IRStr as IRStr


class IRGenerator(MiniDecafVisitor):
    '''
    A visitor for going through the whole ast, inherited from MiniDecafVisitor
    The accept method in different node uses the vistor's different methods, that is the visitor pattern.
    '''
    def __init__(self, irContainer, nameManager):
        self._container = irContainer
        # self.offsetTable = OffsetTable()
        self.labelManager = LabelManager()
        self.nameManager = nameManager
    
    def getPosition(self, term):
        '''
        return the position relative to fp for specific term
        '''
        return self.nameManager[term].offset

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
        self._container.addList([IRStr.Pop()] * self.nameManager.blockSlots[ctx])

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

    def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if ctx.expr() is not None:
                ctx.expr().accept(self) # get expression value
            else:
                self._container.add(IRStr.Const(0)) # default value is zero
            # self.offsetTable.newSlot(var) # new stack space for var
    
    def visitCompound(self, ctx:MiniDecafParser.CompoundContext):
        '''
        visit block here
        pop the variables defined in the block
        '''
        self.visitChildren(ctx)
        self._container.addList([IRStr.Pop()] * self.nameManager.blockSlots[ctx])

        
    def visitWithAsgn(self, ctx:MiniDecafParser.WithAsgnContext):
        ctx.assignment().accept(self)
        if ctx.Ident() is not None:
            # self._container.add(IRStr.FrameSlot(self.offsetTable[ctx.Ident().getText()]))
            self._container.add(IRStr.FrameSlot(self.getPosition(ctx.Ident())))
        else:
            raise Exception('Identifier Not Found')
        # self._computeAddr(ctx.unary())
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
        ctx.logicalOr().accept(self) # calc logicalOr first
        exitLabel = self.labelManager.newLabel("cond_end")
        elseLabel = self.labelManager.newLabel("cond_else")
        self._container.add(IRStr.Branch("beqz", elseLabel)) # if false, go to else
        ctx.expr().accept(self) # if true, do expr
        self._container.addList([IRStr.Branch("br", exitLabel), IRStr.Label(elseLabel)])
        ctx.conditional().accept(self)
        self._container.add(IRStr.Label(exitLabel))

    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        # self._container.add(IRStr.FrameSlot(self.offsetTable[ctx.Ident().getText()]))
        self._container.add(IRStr.FrameSlot(self.getPosition(ctx.Ident()))) # get position from nameManager
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
    


# class OffsetTable(object):
#     '''
#     Referenced to TA's OffsetManager
#     This class aims to note the offset value of every identifier.
#     '''
#     def __init__(self):
#         self._off = {}
#         self._top = 0

#     def __getitem__(self, var):
#         return self._off[var]

#     def newSlot(self, var=None):
#         self._top -= 4
#         if var is not None:
#             if var not in self._off:
#                 self._off[var] = self._top
#             else:
#                 raise Exception("variable redefined")
#         return self._top

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
