from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
from copy import deepcopy
import antlr4
from .IRStr import Unary

class NameParser(MiniDecafVisitor):
    '''
    Name resolution process
    '''
    def __init__(self):
        self.variableScope = StackedScopeManager() # mapping from str -> Variable
        self.scopeVarCnt = [] # number of variables in each block (accumulated count)
        self.totalVarCnt = 0 # totally defined variable count
        # self.nameManager = NameManager()
        self.currentScopeInfo = None
        self.funcNameManager = FuncInfo()

    def defVar(self, ctx, term, numInts=1):
        self.totalVarCnt += numInts # define a new variable, totalVar += 1
        variable = self.variableScope[term.getText()] = Variable(term.getText(), -4 * self.totalVarCnt, 4 * numInts)
        self.currentScopeInfo.bind(term, variable)

    def useVar(self, ctx, term):
        if term is not None:
            variable = self.variableScope[term.getText()]
            self.currentScopeInfo.bind(term, variable)

    def enterScope(self, ctx, is_func = False,isMain=False):
        self.variableScope.push(is_func=is_func, isMain=isMain) # push the ancestor var scope to current
        self.scopeVarCnt.append(self.totalVarCnt) # update the var cnt till now

    def exitScope(self, ctx, ):
        self.currentScopeInfo.blockSlots[ctx] = self.totalVarCnt - self.scopeVarCnt[-1] # calculate the number of variables in current block (nowTotal - ancestorTotal)
        self.totalVarCnt = self.scopeVarCnt[-1] # recover now totalVarCnt to ancestorVarCnt
        self.variableScope.pop() # pop out current block scope
        self.scopeVarCnt.pop() # pop out the ancestor var cnt pushed in enterScope()
    
    
    def declNElems(self, ctx:MiniDecafParser.DeclarationContext):
        def prod(l):
            s = 1
            for i in l:
                s *= i
            return s
        res = prod([int(x.getText()) for x in ctx.Integer()])
        MAX_INT = 2 ** 31 - 1
        if res <= 0 or res >= MAX_INT:
            raise Exception(ctx, "array size <= 0 or too large")
        return res

    def visitCompound(self, ctx:MiniDecafParser.CompoundContext):
        '''
        Visiting a compound structure
        '''
        self.enterScope(ctx)
        self.visitChildren(ctx)
        self.exitScope(ctx)

    def visitProg(self, ctx:MiniDecafParser.ProgContext):
        self.visitChildren(ctx)
        self.funcNameManager.freeze()

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
        self.defVar(ctx, ctx.Ident(), self.declNElems(ctx))

    def visitForDeclStmt(self, ctx:MiniDecafParser.ForDeclStmtContext):
        '''
        process for with declaration
        '''
        self.enterScope(ctx)
        self.visitChildren(ctx)
        self.exitScope(ctx)

    # def visitWithAsgn(self, ctx:MiniDecafParser.WithAsgnContext):
    #     '''
    #     in Minidecaf.g4

    #     assignment
    #     : conditional # noAsgn
    #     | Ident '=' assignment # withAsgn
    #     ;

    #     '''
    #     ctx.assignment().accept(self)  # process the following assignment first! DO NOT LEAVE OUT THIS LINE
    #     if ctx.Ident() is not None:
    #         var = ctx.Ident().getText()
    #         if var not in self.variableScope:
    #             raise Exception(f"undefined reference to {var}")
    #     self.useVar(ctx, ctx.Ident())
    
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

    def func(self, ctx, type_name="def", is_main = False):
        if is_main:
            func = 'main'
        elif ctx.Ident() is not None:
            func = ctx.Ident().getText()

        if type_name == "def":
            if func in self.funcNameManager.nameManager:
                raise Exception(f"redefinition of function {func}")
        currentScope = self.currentScopeInfo = NameManager()
        self.enterScope(ctx, is_func = True, isMain=is_main)
        paramInfo = ParamInfo(ctx.paramList().accept(self))
        if func in self.funcNameManager.paramInfos:
            if not paramInfo.compatible(self.funcNameManager.paramInfos[func]):
                raise Exception(f"conflicting type for {func}")
        if type_name == "def":
            self.funcNameManager.enterFunction(func, currentScope, paramInfo)
            ctx.compound().accept(self)
        elif type_name == "decl":
            if func not in self.funcNameManager.nameManager:
                self.funcNameManager.paramInfos[func] = paramInfo
        self.exitScope(ctx)

    def visitMainFunc(self, ctx:MiniDecafParser.MainFuncContext):
        self.func(ctx, 'def', True)

    def visitFuncDef(self, ctx:MiniDecafParser.FuncDefContext):
        self.func(ctx, "def")

    def visitFuncDecl(self, ctx:MiniDecafParser.FuncDeclContext):
        self.func(ctx, "decl")

    def visitParamList(self, ctx:MiniDecafParser.ParamListContext):
        self.visitChildren(ctx)
        def f(declaration):
            if declaration.Ident() is not None:
                return self.variableScope[declaration.Ident().getText()]
        return list(map(f, ctx.declaration()))
    
    def globalInitializer(self, ctx:MiniDecafParser.ExprContext):
        '''
        global variable init value getter
        '''
        def safeEval(s:str):
            from ast import literal_eval
            return literal_eval(s)
        if ctx is None:
            return None
        try:
            return eval(ctx.getText(), {}, {})
        except:
            raise Exception("global initializers must be constants")

    def visitDeclExternalDecl(self, ctx:MiniDecafParser.DeclExternalDeclContext):
        '''
        global variable declarations
        '''
        ctx = ctx.declaration()
        init = self.globalInitializer(ctx.expr()) # try to get init value
        if ctx.Ident() is not None:
            varStr = ctx.Ident().getText()
            var = Variable(varStr, None, 4 * self.declNElems(ctx))
            globInfo = GlobInfo(var, 4 * self.declNElems(ctx), init)
            if varStr in self.variableScope.currentScopeDict():
                prevVar = self.variableScope[varStr]
                prevGlobInfo = self.funcNameManager.globInfos[prevVar]
                if not prevGlobInfo.compatible(globInfo):
                    raise Exception(f"conflicting types for {varStr}")
                if prevGlobInfo.init is not None:
                    if globInfo.init is not None:
                        raise Exception(f"redefinition of variable {varStr}")
                    return
                elif globInfo.init is not None:
                    self.funcNameManager.globInfos[prevVar].init = init
            else:
                self.variableScope[varStr] = var
                self.funcNameManager.globInfos[var] = globInfo
                self.funcNameManager.globs[varStr] = globInfo
                self.funcNameManager.globsTerm2Var[ctx.Ident()] = var

class Variable:
    '''
    Referenced to TA's implementation
    Variable with name, id, offset.
    Offset here is used for positioning variable place in stack
    '''
    _varTable = {}
    def __init__(self, name:str, offset:int, size:int=4):
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
        self.size = size

    def __eq__(self, other):
        return self.id == other.id and self.name == other.name and self.offset == other.offset and self.size == other.size
    def __str__(self):
        return f"{self.name}({self.id})"
    def __repr__(self):
        return self.__str__()
    def __hash__(self):
        return hash((self.name, self.id, self.offset, self.size))

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
        self.isFuncList = []
        self.isMainList = []

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return '\nglobalScope: '+ str(self.globalScope) + '\n' + 'currentScope:' + str(self.currentScope)
    
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

    def push(self, is_func=False, isMain=False):
        '''
        copy the previous global scope element to the new global scope element
        create the empty current scope element
        '''
        self.isFuncList.append(is_func)
        self.isMainList.append(isMain)
        if len(self.isFuncList) > 1 and self.isFuncList[-2] and not self.isMainList[-2]:
            self.currentScope.append(deepcopy(self.globalScope[-1]))
        else:
            self.currentScope.append({})

        # self.currentScope.append({})
        self.globalScope.append(deepcopy(self.globalScope[-1]))
        # print(self.currentScope)
        # print(self.globalScope)

    def pop(self):
        '''
        pop out the global scope and current scope in the current block        
        '''
        assert len(self.globalScope) > 1
        self.globalScope.pop()
        self.currentScope.pop()
        self.isFuncList.pop()

    def currentScopeDict(self, last=0):
        '''
        return current scope vars
        for redefinition check
        '''
        return self.currentScope[-1-last]

class ParamInfo:
    '''
    parameter list manager
    '''
    def __init__(self, vars:[Variable]):
        self.vars = vars
        self.paramNum = len(vars)

    def compatible(self, other):
        return self.paramNum == other.paramNum


class FuncInfo:
    '''
    Parser for function and global var
    Ref to TA's implementation
    '''
    def __init__(self):
        self.nameManager = {} # str -> NameManager. Initialized by Def.
        self.paramInfos = {} # str -> ParamInfo. Fixed by Def; can be initialized by Decl.
        self.globInfos = {} # Variable -> GlobInfo.
        self.term2Var = {}
        self.globs = {} # str -> GlobInfo
        self.globsTerm2Var = {} # term -> Var

    def enterFunction(self, func:str, funcNameInfo: NameManager, paramInfo:ParamInfo):
        self.nameManager[func] = funcNameInfo
        self.paramInfos[func] = paramInfo

    def freeze(self):
        for funcNameInfo in self.nameManager.values():
            self.term2Var.update(funcNameInfo.term2Var)

    def __getitem__(self, ctx):
        return self.term2Var[ctx]

class GlobInfo:
    '''
    global variable info
    '''
    def __init__(self, var:Variable, size:int, init=None):
        self.var = var
        self.size = size
        self.init = init # not a byte array -- that requires endian info
    def compatible(self, other):
        return True
