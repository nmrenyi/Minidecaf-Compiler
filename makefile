ANTLR_JAR ?= /usr/local/lib/antlr-4.8-complete.jar

grammar-py:
	cd minidecaf && java -jar $(ANTLR_JAR) -Dlanguage=Python3 -visitor -o generated MiniDecaf.g4
