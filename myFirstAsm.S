	.text
	.globl main
main:
	addi sp, sp, -4
	li t1, 100
	sw t1, 0(sp)

	lw a0, 0(sp)
	addi sp, sp, 4

	jr ra
