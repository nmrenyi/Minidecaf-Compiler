# Generated from MiniDecaf.g4 by ANTLR 4.8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\r")
        buf.write("R\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\3\2\3\2\3\2\3\2\3\2\3\3\3\3\3\4\3\4\3")
        buf.write("\5\3\5\3\6\3\6\3\7\3\7\3\7\3\7\3\b\3\b\3\b\3\b\3\b\3\b")
        buf.write("\3\b\3\t\3\t\3\n\6\n;\n\n\r\n\16\n<\3\13\6\13@\n\13\r")
        buf.write("\13\16\13A\3\13\3\13\3\f\3\f\7\fH\n\f\f\f\16\fK\13\f\3")
        buf.write("\r\3\r\3\16\3\16\3\17\3\17\2\2\20\3\3\5\4\7\5\t\6\13\7")
        buf.write("\r\b\17\t\21\n\23\13\25\f\27\r\31\2\33\2\35\2\3\2\6\5")
        buf.write("\2\13\f\17\17\"\"\5\2C\\aac|\6\2\62;C\\aac|\3\2\62;\2")
        buf.write("Q\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13")
        buf.write("\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3")
        buf.write("\2\2\2\2\25\3\2\2\2\2\27\3\2\2\2\3\37\3\2\2\2\5$\3\2\2")
        buf.write("\2\7&\3\2\2\2\t(\3\2\2\2\13*\3\2\2\2\r,\3\2\2\2\17\60")
        buf.write("\3\2\2\2\21\67\3\2\2\2\23:\3\2\2\2\25?\3\2\2\2\27E\3\2")
        buf.write("\2\2\31L\3\2\2\2\33N\3\2\2\2\35P\3\2\2\2\37 \7o\2\2 !")
        buf.write("\7c\2\2!\"\7k\2\2\"#\7p\2\2#\4\3\2\2\2$%\7*\2\2%\6\3\2")
        buf.write("\2\2&\'\7+\2\2\'\b\3\2\2\2()\7}\2\2)\n\3\2\2\2*+\7\177")
        buf.write("\2\2+\f\3\2\2\2,-\7k\2\2-.\7p\2\2./\7v\2\2/\16\3\2\2\2")
        buf.write("\60\61\7t\2\2\61\62\7g\2\2\62\63\7v\2\2\63\64\7w\2\2\64")
        buf.write("\65\7t\2\2\65\66\7p\2\2\66\20\3\2\2\2\678\7=\2\28\22\3")
        buf.write("\2\2\29;\5\35\17\2:9\3\2\2\2;<\3\2\2\2<:\3\2\2\2<=\3\2")
        buf.write("\2\2=\24\3\2\2\2>@\t\2\2\2?>\3\2\2\2@A\3\2\2\2A?\3\2\2")
        buf.write("\2AB\3\2\2\2BC\3\2\2\2CD\b\13\2\2D\26\3\2\2\2EI\5\31\r")
        buf.write("\2FH\5\33\16\2GF\3\2\2\2HK\3\2\2\2IG\3\2\2\2IJ\3\2\2\2")
        buf.write("J\30\3\2\2\2KI\3\2\2\2LM\t\3\2\2M\32\3\2\2\2NO\t\4\2\2")
        buf.write("O\34\3\2\2\2PQ\t\5\2\2Q\36\3\2\2\2\6\2<AI\3\b\2\2")
        return buf.getvalue()


class MiniDecafLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    T__7 = 8
    Integer = 9
    Whitespace = 10
    Ident = 11

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'main'", "'('", "')'", "'{'", "'}'", "'int'", "'return'", "';'" ]

    symbolicNames = [ "<INVALID>",
            "Integer", "Whitespace", "Ident" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "Integer", "Whitespace", "Ident", "IdentLead", 
                  "WordChar", "Digit" ]

    grammarFileName = "MiniDecaf.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.8")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


