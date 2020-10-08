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
    : unary
    ;

unary
    : int_unit
    | unaryOp unary
    ;

unaryOp
    : '-' | '!' | '~'
    ;

int_unit
    : Integer
    ;
