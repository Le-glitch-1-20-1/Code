CC          := gcc
CFLAGS      := -Wall -Wextra -Werror -Wunused -I include/
LDFLAGS     := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11

SRC_DIR     := src
OBJ_DIR     := o
NAME        := game-of-life

# Liste des .c
SRC         := $(wildcard $(SRC_DIR)/*.c)

# Transformation en .o dans o/
OBJ         := $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRC))

# Règle par défaut
all: $(NAME)

# Création de l'exécutable
$(NAME): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(NAME) $(LDFLAGS)

# Compilation des .c vers .o dans o/
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Création du dossier o/ si absent
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

# Nettoyage
clean:
	rm -rf $(OBJ_DIR)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re
