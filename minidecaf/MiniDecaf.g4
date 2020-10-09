// using grammar from TA's reference implementation
grammar MiniDecaf;

import CommonLex;

prog
    : func EOF  // Add EOF for tailing trash
    ;

func
    : ty 'main' '(' ')' '{' stmt* '}'
    ;

ty
    : 'int'
    ;

stmt
    : 'return' expr ';'  # returnStmt
    | expr? ';'  # exprStmt
    | declaration # declStmt
    | ';' # nullStmt
    ;

expr
    : assignment
    ;

assignment
    : logicalOr # noAsgn
    | Ident '=' assignment # withAsgn
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
