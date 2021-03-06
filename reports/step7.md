# Step7 Report

## 2018011423 任一

### 实验内容

在本次实验中，我完整阅读并学习了实验参考书中的内容，并且加入了名词解析的内容。具体来说，我修改了`.g4`文件，加入了块语句的内容，完善了语法。此外，我在语法分析和IR生成之间，加入了名词解析的内容。类似IR生成时的Visitor遍历，在名词解析时我同样进行了AST的遍历，在这个过程中处理了变量作用域等的问题。

具体来说，我设置了一个从`antlr4.tree.Tree.TerminalNodeImpl`类到`Variable`类的映射词典，`Variable`类当中存储着当前节点对应的变量相对fp的偏移量，这样在生成IR时，即使出现了变量重名，也能访问到对应的变量。

在构造这样的一个映射词典时，需要考虑不同作用域下变量重名的问题，这部分我参考了助教的实现，即使用两个存放着词典的栈，来保存全局作用域中的变量和当前作用域中的变量。



### 思考题

1. Q: 请将下述 MiniDecaf 代码中的 `???` 替换为一个 32 位整数，使得程序运行结束后会返回 0

   ```c
int main() {
    int x = ???;
    if (x) {
        return x;
    } else {
        int x = 2;
    }
    return x;
   }
   ```
   
   A: 将 `???` 替换为`0`，即可使程序运行结束返回0.
   
   
   
2. Q: 试问被编译的语言有什么特征时，名称解析作为单独的一个阶段在 IR 生成之前执行会更好？

   A: 被编译的语言存在namespace时，最好先做名词解析再做IR，否则在IR生成时，需要调用某个namespace中的变量`x`时，`x`可能还没有经过名词解析，也就没有在栈上分配过空间，这时对于编译器来说就很难确定这个变量在栈上的位置从而很难完成编译。

### 复用代码情况

本次实验中，我主要参考了助教的名词解析部分，具体来说有栈式作用域管理器、变量的数据结构`Variable`、从AST`antlr4.tree.Tree.TerminalNodeImpl`到`Variable`的映射。

名词解析这部分难度较大，我阅读并充分理解了助教的参考实现，并根据自己的理解结合助教的参考实现，完成了step7。在`NameParser.py`中，我加入了非常充分的注释，以帮助自己学习和加深理解。

