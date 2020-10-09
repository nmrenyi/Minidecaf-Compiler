# Step5 Report

## 2018011423 任一

### 实验内容

在本次实验中，我完整阅读并学习了实验参考书中的内容，并且加入了局部变量和赋值的内容。具体来说，我修改了`.g4`文件，加入了expression和statement等内容，完善了语法。此外，在`IRGenerator.py`当中，我加入了处理变量的声明、赋值等操作的Visitor函数，加入了变量的符号表。我也在`AsmGenerator.py`当中，加入了Prologue和Epilogue的生成相关代码。



### 思考题

1. Q: 描述程序运行过程中函数栈帧的构成，分为哪几部分？每部分所用的空间最少是多少？

   A: 程序运行过程中的函数的栈帧分为以下几部分(由高地址到低地址)：函数返回值地址、old fp、局部变量、表达式运算栈。其中函数返回值占4Byte，old fp占4Byte，局部变量最少是0Byte，表达式运算栈最少是0Byte。

2. Q: 如果 MiniDecaf 也允许多次定义同名变量，并规定新的定义会覆盖之前的同名定义，请问在你的实现中，需要对定义变量和查找变量的逻辑做怎样的修改？

   A: 查找变量的逻辑不需要修改。定义变量时，无需考虑新定义的变量是否在之前定义过，例如变量表是一个Dict，以变量名为key，相对fp的偏移为value，则直接用新的偏移量覆盖之前的即可。下面是我的代码中，变量表管理类的定义，该定义允许了同名变量重复定义。

   ```python
   class OffsetTable(object):
       '''
       允许同名变量重复定义
       '''
       def __init__(self):
           self._off = {}
           self._top = 0
       def __getitem__(self, var):
           return self._off[var]
       def newSlot(self, var=None):
           self._top -= 4
           if var is not None:
               self._off[var] = self._top
           return self._top
   
   ```

   

### 复用代码情况

本次实验内容内容难度较之前偏大，我学习了助教的参考实现，结合参考实现和我自己的理解完成了step5. 我主要参考和学习的内容是有关声明、定义部分的Visitor实现方法，prologue和epilogue的实现以及变量表的数据结构。在进行了一定的参考和学习时，我也在必要的关键处加入了详细的注释，以加深自己的印象和理解。