from copy import deepcopy

import antlr4

from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor


class NameParser(MiniDecafVisitor):
    """
    Name resolution process
    """

    def __init__(self):
        self.variableScope = StackedScopeManager()  # mapping from str -> Variable
        self.scopeVarCnt = []  # number of variables in each block (accumulated count)
        self.totalVarCnt = 0  # totally defined variable count
        self.currentScopeInfo = None
        self.funcNameManager = FuncInfo() # the value to be returned from NameParse period

    def def_var(self, ctx, term, numInts=1):
        self.totalVarCnt += numInts  # define a new variable, totalVar += 1
        variable = self.variableScope[term.getText()] = Variable(term.getText(), -4 * self.totalVarCnt, 4 * numInts)
        self.currentScopeInfo.bind(term, variable)

    def use_var(self, ctx, term):
        if term is not None:
            variable = self.variableScope[term.getText()]
            self.currentScopeInfo.bind(term, variable)

    def enter_scope(self, ctx, is_func=False, isMain=False):
        """
        :param ctx:
        :param is_func:
        :param isMain:
        :return:
        """
        self.variableScope.push(is_func=is_func, isMain=isMain)  # push the ancestor var scope to current
        self.scopeVarCnt.append(self.totalVarCnt)  # update the var cnt till now

    def exit_scope(self, ctx, ):
        self.currentScopeInfo.blockSlots[ctx] = self.totalVarCnt - self.scopeVarCnt[
            -1]  # calculate the number of variables in current block (nowTotal - ancestorTotal)
        self.totalVarCnt = self.scopeVarCnt[-1]  # recover now totalVarCnt to ancestorVarCnt
        self.variableScope.pop()  # pop out current block scope
        self.scopeVarCnt.pop()  # pop out the ancestor var cnt pushed in enterScope()

    def decl_n_elems(self, ctx: MiniDecafParser.DeclarationContext):
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

    def visitCompound(self, ctx: MiniDecafParser.CompoundContext):
        """
        Visiting a compound structure
        """
        self.enter_scope(ctx)
        self.visitChildren(ctx)
        self.exit_scope(ctx)

    def visitProg(self, ctx: MiniDecafParser.ProgContext):
        self.visitChildren(ctx)
        self.funcNameManager.freeze() # collect all the used variables

    def visitDeclaration(self, ctx: MiniDecafParser.DeclarationContext):
        """
        in Minidecaf.g4

        declaration
        : ty Ident ('=' expr)? ';'
        ;
        """

        if ctx.expr() is not None:
            ctx.expr().accept(self)
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var in self.variableScope.current_scope_dict():
                raise Exception(f"redefinition of {var}")  # redefinition of vars
        self.def_var(ctx, ctx.Ident(), self.decl_n_elems(ctx))

    def visitForDeclStmt(self, ctx: MiniDecafParser.ForDeclStmtContext):
        """
        process for with declaration
        """
        self.enter_scope(ctx)
        self.visitChildren(ctx)
        self.exit_scope(ctx)

    def visitAtomIdent(self, ctx: MiniDecafParser.AtomIdentContext):
        """
        in Minidecaf.g4

        atom
            : Integer # atomInteger
            | '(' expr ')' # atomParen
            | Ident # atomIdent
            ;

        """
        if ctx.Ident() is not None:
            var = ctx.Ident().getText()
            if var not in self.variableScope:
                raise Exception(f"undefined reference to {var}")
        self.use_var(ctx, ctx.Ident())

    def func(self, ctx, type_name="def", is_main=False):
        if is_main:
            func = 'main' # main func do not have Ident() attribute
        elif ctx.Ident() is not None:
            func = ctx.Ident().getText()

        if type_name == "def":
            if func in self.funcNameManager.nameManager:  # redefinition of functions is prohibited
                raise Exception(f"redefinition of function {func}")
        current_scope = self.currentScopeInfo = NameManager()
        self.enter_scope(ctx, is_func=True, isMain=is_main)
        paramInfo = ParamInfo(ctx.paramList().accept(self))
        if func in self.funcNameManager.paramInfos: # the function has been declared before
            if not paramInfo.compatible(self.funcNameManager.paramInfos[func]):
                raise Exception(f"conflicting type for {func}")
        if type_name == "def":
            self.funcNameManager.enter_function(func, current_scope, paramInfo)
            ctx.compound().accept(self)
        elif type_name == "decl":
            if func not in self.funcNameManager.nameManager:
                self.funcNameManager.paramInfos[func] = paramInfo
        self.exit_scope(ctx)

    def visitMainFunc(self, ctx: MiniDecafParser.MainFuncContext):
        self.func(ctx, 'def', True)

    def visitFuncDef(self, ctx: MiniDecafParser.FuncDefContext):
        self.func(ctx, "def")

    def visitFuncDecl(self, ctx: MiniDecafParser.FuncDeclContext):
        self.func(ctx, "decl")

    def visitParamList(self, ctx: MiniDecafParser.ParamListContext):
        self.visitChildren(ctx)

        def f(declaration):
            if declaration.Ident() is not None:
                return self.variableScope[declaration.Ident().getText()]

        return list(map(f, ctx.declaration()))

    def global_initializer(self, ctx: MiniDecafParser.ExprContext):
        """
        global variable init value getter
        """

        if ctx is None:
            return None
        try:
            return eval(ctx.getText(), {}, {})
        except:
            raise Exception("global initializers must be constants")

    def visitDeclExternalDecl(self, ctx: MiniDecafParser.DeclExternalDeclContext):
        """
        global variable declarations
        """
        ctx = ctx.declaration()
        init = self.global_initializer(ctx.expr())  # try to get init value, maybe None or Int
        if ctx.Ident() is not None:
            varStr = ctx.Ident().getText()
            var = Variable(varStr, None, 4 * self.decl_n_elems(ctx))
            globInfo = GlobInfo(var, 4 * self.decl_n_elems(ctx), init)
            if varStr in self.variableScope.current_scope_dict():
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
    """
    Referenced to TA's implementation
    Variable with name, id, offset.
    Offset here is used for positioning variable place in stack
    """
    _varTable = {}

    def __init__(self, name: str, offset: int, size: int = 4):
        """
        name : the name of the variable
        offset: the position offset of the variable  to fp (usually negative)
        id: to identify different variable in different scopes with same name
        """
        if name not in self._varTable:
            self._varTable[name] = 0
        else:
            self._varTable[name] += 1
        self.id = self._varTable[name]  # a(0) and a(1) are different variables in different scopes
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
    """
    NameManager
    Referenced to TA's implementation
    """

    def __init__(self):
        self.term2Var = {}  # mappping from term -> Variable
        self.blockSlots = {}  # mapping CompoundContext/ForDeclStmtContext -> int(cnt of variables in the block)

    def bind(self, term: antlr4.tree.Tree.TerminalNodeImpl, var: Variable):
        """
        create mapping from term to variable
        """
        # print('bind', term, term.__repr__())
        self.term2Var[term] = var

    def __getitem__(self, term: antlr4.tree.Tree.TerminalNodeImpl):
        """
        return the corresponding variable of the term
        """
        # print('wanna', term, term.__repr__())
        # print('all', self.term2Var)
        return self.term2Var[term]


class StackedScopeManager:
    """
    Scope Manager
    Reference to TA's implementation

    """

    def __init__(self):
        """
        contains 2 list of dict
        the dict have variable name as key, the variable object as the value
        """
        self.globalScope = [{}]  # global var scope list (accumulative)
        self.currentScope = [{}]  # local var scope list
        self.isFuncList = []  # the list for if the current scope and previous scope is a function scope
        self.isMainList = []  # the list for if the current scope and previous scope is a main function scope

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '\nglobalScope: ' + str(self.globalScope) + '\n' + 'currentScope:' + str(self.currentScope)

    def __getitem__(self, name: str):
        """
        return the Variable object corresponding to the variable name
        """
        return self.globalScope[-1][name]

    def __setitem__(self, name: str, value: Variable):
        """
        set the mapping from name to the Variable object
        """
        self.currentScope[-1][name] = self.globalScope[-1][name] = value

    def __contains__(self, name: str):
        """
        check if the variable name is in the whole scope
        for undefined reference check
        """
        return name in self.globalScope[-1]

    def __len__(self):
        return len(self.globalScope[-1])

    def push(self, is_func=False, isMain=False):
        """
        copy the previous global scope element to the new global scope element
        create the empty current scope element
        """
        self.isFuncList.append(is_func)
        self.isMainList.append(isMain)
        if len(self.isFuncList) > 1 and self.isFuncList[-2] and not self.isMainList[-2]:
            """
            if the previous scope is a function except main function, then the parameter list should be considered in 
            the current function scope
            
            if the previous scope is main function, since main functions do not have arguments in minidecaf, 
            we shouldn't include the previous variabel scope into current (or the global vars will be considered 
            as main function scope variables.
            """
            self.currentScope.append(deepcopy(self.globalScope[-1]))
        else:
            self.currentScope.append({})

        self.globalScope.append(deepcopy(self.globalScope[-1]))

    def pop(self):
        """
        pop out the global scope and current scope in the current block
        """
        assert len(self.globalScope) > 1
        self.globalScope.pop()
        self.currentScope.pop()
        self.isFuncList.pop()

    def current_scope_dict(self, last=0):
        """
        return current scope vars
        for redefinition check
        """
        return self.currentScope[-1 - last]


class ParamInfo:
    """
    parameter list manager
    """

    def __init__(self, variables: [Variable]):
        self.vars = variables
        self.paramNum = len(variables)

    def compatible(self, other):
        return self.paramNum == other.paramNum


class FuncInfo:
    """
    Parser for function and global var
    Ref to TA's implementation
    """

    def __init__(self):
        self.nameManager = {}  # str -> NameManager. Initialized by Def.
        self.paramInfos = {}  # str -> ParamInfo. Fixed by Def; can be initialized by Decl.
        self.globInfos = {}  # Variable -> GlobInfo.
        self.term2Var = {} # term -> Var
        self.globs = {}  # str -> GlobInfo
        self.globsTerm2Var = {}  # term -> Var

    def enter_function(self, func: str, funcNameInfo: NameManager, paramInfo: ParamInfo):
        self.nameManager[func] = funcNameInfo
        self.paramInfos[func] = paramInfo

    def freeze(self):
        """
        get all the used function vars into term2Var
        :return: None
        """
        for funcNameInfo in self.nameManager.values():
            self.term2Var.update(funcNameInfo.term2Var)

    def __getitem__(self, ctx):
        return self.term2Var[ctx]


class GlobInfo:
    """
    global variable info
    """

    def __init__(self, var: Variable, size: int, init=None):
        self.var = var
        self.size = size
        self.init = init  # not a byte array -- that requires endian info

    def compatible(self, other):
        return True
