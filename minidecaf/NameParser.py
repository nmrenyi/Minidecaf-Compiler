from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
from copy import deepcopy

class NameParser(MiniDecafVisitor):
    """
    Name resolution.
    It is basically an alpha conversion pass; different variables with the same
    name are resolved to different `Variable`s. The output is a NameInfo, mapping
    variable occurrence (i.e. its Ident's TerminalNodeImpl) to Variable/Offsets.
    """
    def __init__(self):
        self.variableScope = StackedScopeManager() # str -> Variable
        self.scopeVarCnt = [] # number of variables in each block (accumulated count)
        self.totalVarCnt = 0 # totally defined variable count
        self.nameManager = NameManager()

    def defVar(self, ctx, term):
        self.totalVarCnt += 1 # define a new variable
        var = self.variableScope[term.getText()] = Variable(term.getText(), -4 * self.totalVarCnt)
        self.nameManager.bind(term, var)

    def useVar(self, ctx, term):
        if term is not None:
            var = self.variableScope[term.getText()]
            self.nameManager.bind(term, var)

    def enterScope(self, ctx):
        self.variableScope.push() # push the ancestor var scope to current
        self.scopeVarCnt.append(self.totalVarCnt)

    def exitScope(self, ctx):
        self.nameManager.blockSlots[ctx] = self.totalVarCnt - self.scopeVarCnt[-1] # count current block variables
        self.totalVarCnt = self.scopeVarCnt[-1] # save ancestor block variables
        self.variableScope.pop()
        self.scopeVarCnt.pop()

    def visitCompound(self, ctx:MiniDecafParser.CompoundContext):
        self.enterScope(ctx)
        self.visitChildren(ctx)
        self.exitScope(ctx)

    def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
        if ctx.expr() is not None:
            ctx.expr().accept(self)
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var in self.variableScope.currentScopeDict():
                raise Exception(f"redefinition of {var}") # redefinition of vars
        self.defVar(ctx, ctx.Ident())

    # def visitForDeclStmt(self, ctx:MiniDecafParser.ForDeclStmtContext):
    #     self.enterScope(ctx)
    #     self.visitChildren(ctx)
    #     self.exitScope(ctx)

    def visitWithAsgn(self, ctx:MiniDecafParser.WithAsgnContext):
        ctx.assignment().accept(self)  # process the following assignment first! DO NOT LEAVE OUT THIS LINE
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var not in self.variableScope:
                raise Exception(f"undefined reference to {var}")
        self.useVar(ctx, ctx.Ident())
    
    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var not in self.variableScope:
                raise Exception(f"undefined reference to {var}")
        self.useVar(ctx, ctx.Ident())


class Variable:
    '''
    Referenced to TA's implementation
    Variable with name, offset.
    Offset here is used for positioning variable place in stack
    '''
    _varTable = {}
    def __init__(self, ident:str, offset:int):
        if ident not in self._varTable:
            self._varTable[ident] = 0
        else:
            self._varTable[ident] += 1
        self.id = self._varTable[ident]
        self.ident = ident
        self.offset = offset

    def __eq__(self, other):
        return self.id == other.id and self.ident == other.ident and\
            self.offset == other.offset
    def __str__(self):
        return f"{self.ident}({self.id})"
    def __repr__(self):
        return self.__str__()
    def __hash__(self):
        return hash((self.ident, self.id, self.offset))

class NameManager:
    def __init__(self):
        self.term2Var = {}    # term -> Variable
        self.blockSlots = {} # BlockContext / ForDeclStmtContext -> int >= 0

    def bind(self, term, var):
        # print('bind', term, term.__repr__())
        self.term2Var[term] = var

    def __getitem__(self, term):
        # print('wanna', term, term.__repr__())
        # print('all', self.term2Var)
        return self.term2Var[term]

class StackedScopeManager:
    def __init__(self):
        self.globalScope = [{}] # global var scope list (accumulative)
        self.currentScope = [{}] # local var scope list

    def __getitem__(self, key):
        return self.globalScope[-1][key]

    def __setitem__(self, key, value):
        self.currentScope[-1][key] = self.globalScope[-1][key] = value

    def __contains__(self, key):
        return key in self.globalScope[-1]

    def __len__(self):
        return len(self.globalScope[-1])

    def push(self):
        self.globalScope.append(deepcopy(self.globalScope[-1]))
        self.currentScope.append({})

    def pop(self):
        assert len(self.globalScope) > 1
        self.globalScope.pop()
        self.currentScope.pop()

    def currentScopeDict(self, last=0):
        '''
        return current scope vars
        for redefinition check
        '''
        return self.currentScope[-1-last]
