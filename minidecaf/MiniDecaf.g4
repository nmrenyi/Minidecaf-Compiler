grammar MiniDecaf;

import CommonLex;

prog
    : externalDecl+ EOF  // Add EOF for tailing trash
    ;

externalDecl
    : func* main_func func* # funcExternalDecl
    | declaration ';' # declExternalDecl
    ;

main_func
    : ty 'main' '(' paramList ')' compound # mainFunc
    ;

func
    : ty Ident '(' paramList ')' compound # funcDef
    | ty Ident '(' paramList ')' ';' # funcDecl
    ;

paramList
    : (declaration (',' declaration)*)?
    ;

argList
    : (expr (',' expr)*)?
    ;

ty
    : 'int' # intType
    | ty '*' # ptrType

    ;

stmt
    : 'return' expr ';'  # returnStmt
    | expr? ';'  # exprStmt
    | ';' # nullStmt
    | 'if' '(' expr ')' th=stmt ('else' el=stmt)? # ifStmt
    | compound # cmpdStmt
    | 'for' '(' init=declaration  ctrl=expr? ';' post=expr? ')' stmt # forDeclStmt
    | 'for' '(' init=expr? ';' ctrl=expr? ';' post=expr? ')' stmt # forStmt
    | 'while' '(' expr ')' stmt # whileStmt
    | 'do' stmt 'while' '(' expr ')' ';' # doWhileStmt
    | 'break' ';' # breakStmt
    | 'continue' ';' # continueStmt
    ;

compound
    : '{' blockItem* '}'
    ;

blockItem
    : stmt
    | declaration
    ;

expr
    : assignment
    ;

assignment
    : conditional # noAsgn
    | unary asgnOp assignment # withAsgn
    ;

conditional
    : logicalOr # noCond
    | logicalOr '?' expr ':' conditional # withCond
    ;

declaration
    : ty Ident ('[' Integer ']')* ('=' expr)? ';'?
    ;

// decl_no_semiCol
//     : ty Ident ('=' expr)?
//     ;

unary
    : postfix # tUnary
    | unaryOp cast # cUnary
    ;

cast
    : unary # tCast
    | '(' ty ')' cast # cCast
    ;

postfix
    : 
    Ident '(' argList ')' # postfixCall
    | atom # tPostfix
    | postfix '[' expr ']' # postfixArray
    ;
    
unaryOp
    : '-' | '!' | '~' | '*' | '&'
    ;

atom
    : Integer # atomInteger
    | '(' expr ')' # atomParen
    | Ident # atomIdent
    // | Ident '(' argList ')' # atomCall
    ;

additive
    : multiplicative # tAdd
    | additive addOp multiplicative # cAdd
    ;

multiplicative
    : cast # tMul
    | multiplicative mulOp cast # cMul
    ;

equality
    : relational # tEq
    | equality eqOp relational # cEq
    ;

relational
    : additive # tRel
    | relational relOp additive # cRel
    ;

logicalOr
    : logicalAnd # tLor
    | logicalOr orOp logicalAnd # cLor
    ;

logicalAnd
    : equality # tLand
    | logicalAnd andOp equality # cLand
    ;

orOp
    : '||'
    ;

andOp
    : '&&'
    ;

addOp
    : '+' | '-'
    ;

mulOp
    : '*' | '/' | '%'
    ;

relOp
    : '<' | '>' | '<=' | '>='
    ;

eqOp
    : '==' | '!='
    ;

asgnOp
    : '='
    ;
