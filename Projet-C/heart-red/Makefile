CC            := gcc
CC_WIN        := x86_64-w64-mingw32-gcc
CFLAGS        := -Wall -Wextra -Werror -Wunused
LDFLAGS       := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11
WIN_INCLUDES  := -I/home/le-glitch/raylib/raylib-windows/src
WIN_LIBPATH   := -L/home/le-glitch/raylib/raylib-windows/src
WIN_LDFLAGS   := -lraylib -lopengl32 -lgdi32 -lwinmm

OBJ_DIR       := o
NAME          := heart-red

# Liste des .c
SRC           := $(wildcard *.c)

# Transformation en .o dans o/
OBJ           := $(patsubst %.c, $(OBJ_DIR)/%.o, $(SRC))

# Regle par defaut :
#  - compile toujours Linux en premier
#  - si echec -> make s'arrete, Windows n'est PAS propose
#  - si succes -> demande si on compile aussi pour Windows
all: $(NAME)
	@read -p ">> Compiler aussi pour Windows ? [y/N] " rep; \
	if [ "$$rep" = "y" ] || [ "$$rep" = "Y" ]; then \
		$(MAKE) --no-print-directory windows; \
	else \
		echo ">> Build Windows annule."; \
	fi

# Creation de l'executable Linux
$(NAME): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(NAME) $(LDFLAGS)

# Compilation des .c vers .o dans o/
$(OBJ_DIR)/%.o: %.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Creation du dossier o/ si absent
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

# Build Windows (.exe, sans console), appele uniquement si demande
.PHONY: windows
windows: $(SRC)
	$(CC_WIN) $(CFLAGS) $(SRC) -o $(NAME).exe \
		-mwindows -Wl,--subsystem,windows \
		$(WIN_INCLUDES) $(WIN_LIBPATH) $(WIN_LDFLAGS)
	@echo ">> Build Windows termine -> $(NAME).exe"

# Nettoyage
clean:
	rm -rf $(OBJ_DIR)

fclean: clean
	rm -f $(NAME) $(NAME).exe

re: fclean all

.PHONY: all clean fclean re
