CC            := gcc
CC_WIN        := x86_64-w64-mingw32-gcc
CFLAGS        := -Wall -Wextra -Werror -Wunused -I include/
LDFLAGS       := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11
WIN_INCLUDES  := -I/home/le-glitch/Documents/raylib/raylib-windows/src
WIN_LIBPATH   := -L/home/le-glitch/Documents/raylib/raylib-windows/src
WIN_LDFLAGS   := -lraylib -lopengl32 -lgdi32 -lwinmm

SRC_DIR       := src
OBJ_DIR       := o
NAME          := heart-red

# List of .c files
SRC           := $(wildcard $(SRC_DIR)/*.c)

# Transform into .o files in o/
OBJ           := $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRC))

# Default rule:
#  - always builds Linux first
#  - on failure -> make stops, Windows is NOT offered
#  - on success -> asks whether to also build for Windows
all: $(NAME)
	@read -p ">> Also build for Windows? [y/N] " rep; \
	if [ "$$rep" = "y" ] || [ "$$rep" = "Y" ]; then \
		$(MAKE) --no-print-directory windows; \
	else \
		echo ">> Windows build cancelled."; \
	fi

# Creating the Linux executable
$(NAME): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(NAME) $(LDFLAGS)

# Compiling .c files into .o in o/
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Creating the o/ directory if missing
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

# Windows build (.exe, no console), invoked if requested
.PHONY: windows
windows: $(SRC)
	$(CC_WIN) $(CFLAGS) $(SRC) -o $(NAME).exe \
		-mwindows -Wl,--subsystem,windows \
		$(WIN_INCLUDES) $(WIN_LIBPATH) $(WIN_LDFLAGS)
	@echo ">> Windows build finished -> $(NAME).exe"

# Cleanup
clean:
	rm -rf $(OBJ_DIR)

fclean: clean
	rm -f $(NAME) $(NAME).exe

re: fclean all

.PHONY: all clean fclean re
