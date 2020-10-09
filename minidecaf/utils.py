def push_int(val:int):
    return [f"addi sp, sp, -4", f"li t1, {val}", f"sw t1, 0(sp)"] # push int

def push_reg(val:str):
    return [f"addi sp, sp, -4", f"sw {val}, 0(sp)"] # push register

def pop(reg):
    return ([f"lw {reg}, 0(sp)"] if reg is not None else []) + [f"addi sp, sp, 4"]
