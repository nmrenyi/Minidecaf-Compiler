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
    | unary '=' assignment # withAsgn
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
    | unaryOp unary # cUnary
    ;

postfix
    : atom # tPostfix
    | postfix '[' expr ']' # postfixArray
    | Ident '(' argList ')' # postfixCall
    ;
    
unaryOp
    : '-' | '!' | '~' | '*' | '&'
    ;

atom
    : Integer # atomInteger
    | '(' expr ')' # atomParen
    | Ident # atomIdent
    | Ident '(' argList ')' # atomCall
    ;

additive
    : multiplicative
    | additive addOp multiplicative
    ;

multiplicative
    : unary
    | multiplicative mulOp unary
    ;

equality
    : relational
    | equality eqOp relational
    ;

relational
    : additive
    | relational relOp additive
    ;

logicalOr
    : logicalAnd
    | logicalOr orOp logicalAnd
    ;

logicalAnd
    : equality
    | logicalAnd andOp equality
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
