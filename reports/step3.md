# Step3 Report

## 2018011423 任一

### 实验内容

在本次实验中，我完整阅读并学习了实验参考书中的内容，并且加入了有关二元运算符的内容，使我的编译器成功通过了STEP3。具体来说是在`.g4`文件中加入有关加减乘除模运算的语法，在`IRGenerator.py`中加入有关加减乘除模的visitor相关部分。



### 思考题

1. Q: 请给出将寄存器 `t0` 中的数值压入栈中所需的 riscv 汇编指令序列；请给出将栈顶的数值弹出到寄存器 `t0` 中所需的 riscv 汇编指令序列。

   A: 将寄存器 `t0` 中的数值压入栈中:

   ```assembly
   addi sp, sp, -4
   sw t1, 0(sp)
   ```

   ​	将栈顶的数值弹出到寄存器 `t0`:

   ```assembly
   lw t0, 0(sp)
   addi sp, sp, 4
   ```

2. Q: 即使除法的右操作数不是 0，仍然可能存在未定义行为。举例并在自己的机器和RISCV-32的qemu模拟器中运行。

   A: 此时除法的左操作数是`-2147483648`，右操作数是`-1`. 

   因此运行的代码如下

   ```c
   #include <stdio.h>
   int main() {
     int a = -2147483648;
     int b = -1;
     printf("%d\n", a / b);
     return 0;
   }
   ```

   把上述代码保存在`s3.c`中，在本机(x86-64架构)运行，在Windows Cmd中，用`gcc s3.c`编译，用`a.exe`运行，没有输出任何结果。在本机WSL中，使用`gcc s3.c`编译，`./a.out`运行，输出`Floating point exception (core dumped)`.

   

   在 RISCV-32 的 qemu 模拟器中，使用`riscv64-unknown-elf-gcc -march=rv32im -mabi=ilp32  s3.c` 命令编译，使用`qemu-riscv32 a.out`命令运行，得到输出结果`-2147483648`.



### 复用代码情况

在本次实验中，我主要按照实验指导书进行了操作，对样例代码没有直接的参考。
