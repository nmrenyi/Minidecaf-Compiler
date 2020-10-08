// using grammar from TA's reference implementation
grammar MiniDecaf;

import CommonLex;

prog
    : func EOF  // Add EOF for tailing trash
    ;

func
    : ty 'main' '(' ')' '{' stmt '}'
    ;

ty
    : 'int'
    ;

stmt
    : 'return' expr ';' # returnStmt
    ;

expr
    : additive
    ;

unary
    : intUnit
    | unaryOp unary
    ;

unaryOp
    : '-' | '!' | '~'
    ;

intUnit
    : Integer
    | '(' expr ')'
    ;

additive
    : multiplicative
    | additive addOp multiplicative
    ;

multiplicative
    : unary
    | multiplicative mulOp unary
    ;

addOp
    : '+' | '-'
    ;

mulOp
    : '*' | '/' | '%'
    ;
