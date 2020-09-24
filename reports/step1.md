# step1 思考题

## 从零开始的lexer, parser等

1. Q: minilexer 是如何使得 `int` 被分析成一个关键字而非一个标识符的？

   A: minilexer会让每一种tokenKind对当前字符串的开头做匹配，并且选择匹配长度最长的作为结果，若匹配长度相同，则会选取**靠前**的tokenKind作为匹配结果，具体的实现代码是`i, l = max(enumerate(matchResult), key=lambda x:x[1])`，matchResult有多个最大值时，返回的第一个。

   

   由于`Int`在匹配时的顺序比标识符`Identifier`更靠前，因此虽然`int` 在这两种Token匹配时取得的matchLength相等，但是会优先匹配为关键词`Int`，而非`Identifier`.

   

2. Q: 修改 minilexer 的输入（lexer.setInput 的参数），使得 lex 报错，给出一个简短的例子。

   A: 修改输入为中文字符即可使lex报错，例如输入"汉字"这两个中文字符，lex就会报错。

   

4. Q: 修改 minilexer 的输入，使得 lex 不报错但 parser 报错，给出一个简短的例子。

   A: 修改输入为`int main() {return ;}`即可使得lex不报错而parser报错

   

5. Q: 一种暴力算法是：lex 同上但是不进行 parse，而是在 token 流里面寻找连续的 Return，Integer 和 Semicolon，找到以后取得 Integer 的常量 a，然后类似上面目标代码生成。这个暴力算法有什么问题？

   A: 这种算法的问题在于，如果返回的是一个表达式，例如`return (3 + 4) * 5`，则无法进行正确的语法分析，因为这个例子里面, return, Integer和Semicolon并不是相连的.

