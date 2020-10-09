grammar MiniDecaf;

import CommonLex;

prog
    : func EOF  // Add EOF for tailing trash
    ;

func
    : ty 'main' '(' ')' '{' blockItem* '}'
    ;

ty
    : 'int'
    ;

stmt
    : 'return' expr ';'  # returnStmt
    | expr? ';'  # exprStmt
    | ';' # nullStmt
    | 'if' '(' expr ')' th=stmt ('else' el=stmt)? # ifStmt
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
    | Ident '=' assignment # withAsgn
    ;

conditional
    : logicalOr # noCond
    | logicalOr '?' expr ':' conditional # withCond
    ;

declaration
    : ty Ident ('=' expr)? ';'
    ;

unary
    : atom
    | unaryOp unary
    ;

unaryOp
    : '-' | '!' | '~'
    ;

atom
    : Integer # atomInteger
    | '(' expr ')' # atomParen
    | Ident # atomIdent
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
