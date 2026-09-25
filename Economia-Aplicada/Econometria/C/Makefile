CC = gcc
CFLAGS = -Wall -Wextra -O2
BIN_DIR = bin

ALVOS = $(BIN_DIR)/ar1 $(BIN_DIR)/painel_fe $(BIN_DIR)/capm $(BIN_DIR)/diff_in_diff

.PHONY: all limpar

all: $(ALVOS)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BIN_DIR)/ar1: macroeconometria/ar1.c comum/ols.c comum/ols.h | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ macroeconometria/ar1.c comum/ols.c -lm

$(BIN_DIR)/painel_fe: microeconometria/painel_fe.c comum/ols.c comum/ols.h | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ microeconometria/painel_fe.c comum/ols.c -lm

$(BIN_DIR)/capm: financas/capm.c comum/ols.c comum/ols.h | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ financas/capm.c comum/ols.c -lm

$(BIN_DIR)/diff_in_diff: trabalho_desenvolvimento/diff_in_diff.c comum/ols.c comum/ols.h | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ trabalho_desenvolvimento/diff_in_diff.c comum/ols.c -lm

limpar:
	rm -rf $(BIN_DIR)
