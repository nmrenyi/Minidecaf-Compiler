from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
from copy import deepcopy
import antlr4

class NameParser(MiniDecafVisitor):
    """
    Name resolution.
    It is basically an alpha conversion pass; different variables with the same
    name are resolved to different `Variable`s. The output is a NameInfo, mapping
    variable occurrence (i.e. its Ident's TerminalNodeImpl) to Variable/Offsets.
    """
    def __init__(self):
        self.variableScope = StackedScopeManager() # mapping from str -> Variable
        self.scopeVarCnt = [] # number of variables in each block (accumulated count)
        self.totalVarCnt = 0 # totally defined variable count
        self.nameManager = NameManager()

    def defVar(self, ctx, term):
        self.totalVarCnt += 1 # define a new variable, totalVar += 1
        variable = self.variableScope[term.getText()] = Variable(term.getText(), -4 * self.totalVarCnt)
        self.nameManager.bind(term, variable)

    def useVar(self, ctx, term):
        if term is not None:
            variable = self.variableScope[term.getText()]
            self.nameManager.bind(term, variable)

    def enterScope(self, ctx):
        self.variableScope.push() # push the ancestor var scope to current
        self.scopeVarCnt.append(self.totalVarCnt) # update the var cnt till now

    def exitScope(self, ctx):
        self.nameManager.blockSlots[ctx] = self.totalVarCnt - self.scopeVarCnt[-1] # calculate the number of variables in current block (nowTotal - ancestorTotal)
        self.totalVarCnt = self.scopeVarCnt[-1] # recover now totalVarCnt to ancestorVarCnt
        self.variableScope.pop() # pop out current block scope
        self.scopeVarCnt.pop() # pop out the ancestor var cnt pushed in enterScope()

    def visitCompound(self, ctx:MiniDecafParser.CompoundContext):
        '''
        Visiting a compound structure
        '''
        self.enterScope(ctx)
        self.visitChildren(ctx)
        self.exitScope(ctx)

    def visitDeclaration(self, ctx:MiniDecafParser.DeclarationContext):
        '''
        in Minidecaf.g4

        declaration
        : ty Ident ('=' expr)? ';'
        ;
        
        '''
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
        '''
        in Minidecaf.g4

        assignment
        : conditional # noAsgn
        | Ident '=' assignment # withAsgn
        ;

        '''
        ctx.assignment().accept(self)  # process the following assignment first! DO NOT LEAVE OUT THIS LINE
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var not in self.variableScope:
                raise Exception(f"undefined reference to {var}")
        self.useVar(ctx, ctx.Ident())
    
    def visitAtomIdent(self, ctx:MiniDecafParser.AtomIdentContext):
        '''
        in Minidecaf.g4
        
        atom
            : Integer # atomInteger
            | '(' expr ')' # atomParen
            | Ident # atomIdent
            ;

        '''
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var not in self.variableScope:
                raise Exception(f"undefined reference to {var}")
        self.useVar(ctx, ctx.Ident())


class Variable:
    '''
    Referenced to TA's implementation
    Variable with name, id, offset.
    Offset here is used for positioning variable place in stack
    '''
    _varTable = {}
    def __init__(self, name:str, offset:int):
        '''
        name : the name of the variable
        offset: the position offset of the variable  to fp
        id: to identify different variable in different scopes with same name
        '''
        if name not in self._varTable:
            self._varTable[name] = 0
        else:
            self._varTable[name] += 1
        self.id = self._varTable[name] # a(0) and a(1) are different variables in different scopes
        self.name = name
        self.offset = offset

    def __eq__(self, other):
        return self.id == other.id and self.name == other.name and self.offset == other.offset
    def __str__(self):
        return f"{self.name}({self.id})"
    def __repr__(self):
        return self.__str__()
    def __hash__(self):
        return hash((self.name, self.id, self.offset))

class NameManager:
    '''
    NameManager
    Referenced to TA's implementation
    '''
    def __init__(self):
        self.term2Var = {}    # mappping from term -> Variable
        self.blockSlots = {} # mapping CompoundContext/ForDeclStmtContext -> int(cnt of variables in the block)

    def bind(self, term:antlr4.tree.Tree.TerminalNodeImpl, var:Variable):
        '''
        create mapping from term to variable
        '''
        # print('bind', term, term.__repr__())
        self.term2Var[term] = var

    def __getitem__(self, term:antlr4.tree.Tree.TerminalNodeImpl):
        '''
        return the corresponding variable of the term
        '''
        # print('wanna', term, term.__repr__())
        # print('all', self.term2Var)
        return self.term2Var[term]

class StackedScopeManager:
    '''
    Scope Manager
    Reference to TA's implementation
    
    '''
    def __init__(self):
        '''
        contains 2 list of dict
        the dict have variable name as key, the variable object as the value        
        '''
        self.globalScope = [{}] # global var scope list (accumulative)
        self.currentScope = [{}] # local var scope list

    def __getitem__(self, name:str):
        '''
        return the Variable object corresponding to the variable name
        '''
        return self.globalScope[-1][name]

    def __setitem__(self, name:str, value:Variable):
        '''
        set the mapping from name to the Variable object
        '''
        self.currentScope[-1][name] = self.globalScope[-1][name] = value

    def __contains__(self, name:str):
        '''
        check if the variable name is in the whole scope
        for undefined reference check
        '''
        return name in self.globalScope[-1]

    def __len__(self):
        return len(self.globalScope[-1])

    def push(self):
        '''
        copy the previous global scope element to the new global scope element
        create the empty current scope element
        '''
        self.globalScope.append(deepcopy(self.globalScope[-1]))
        self.currentScope.append({})

    def pop(self):
        '''
        pop out the global scope and current scope in the current block        
        '''
        assert len(self.globalScope) > 1
        self.globalScope.pop()
        self.currentScope.pop()

    def currentScopeDict(self, last=0):
        '''
        return current scope vars
        for redefinition check
        '''
        return self.currentScope[-1-last]
