CC            := gcc
CFLAGS        := -Wall -Wextra -Werror -Wunused

OBJ_DIR       := o
NAME          := automake

# Liste des .c
SRC           := $(wildcard *.c)

# Transformation en .o dans o/
OBJ           := $(patsubst %.c, $(OBJ_DIR)/%.o, $(SRC))

# Regle par defaut
all: $(NAME)

# Creation de l'executable Linux
$(NAME): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(NAME)

# Compilation des .c vers .o dans o/
$(OBJ_DIR)/%.o: %.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Creation du dossier o/ si absent
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

# Nettoyage
clean:
	rm -rf $(OBJ_DIR)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re
