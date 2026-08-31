# ==============================================================================
# Generic multi-project Makefile
#
# Behavior:
#   - ALWAYS compiles Linux first, with -Wall -Wextra -Werror -Wunused
#   - If the Linux build fails -> make stops, Windows is NOT offered
#   - If the Linux build succeeds -> asks whether to also build Windows
#       -> "y" : also builds for Windows (no console, "GUI only" .exe)
#       -> anything else: stops, does not build Windows
# ==============================================================================

SHELL := /bin/bash

# --- List of projects ---
PROJECTS := heart-red heart-mult love

# --- Warning flags enforced everywhere ---
WARN_FLAGS := -Wall -Wextra -Werror -Wunused

# --- Default values (used when a project doesn't override anything) ---
DEFAULT_CC_LINUX   := gcc
DEFAULT_CC_WIN     := x86_64-w64-mingw32-gcc
DEFAULT_LIBS_LINUX :=
DEFAULT_LIBS_WIN   :=
DEFAULT_INCLUDES   :=
DEFAULT_LIBPATH    :=
DEFAULT_SRC        := main.c

# ==============================================================================
# Per-project specific config
# ==============================================================================
# Convention: <project_name>_<KEY> = value
# Available keys: SRC, CC_LINUX, CC_WIN,
#   INCLUDES_LINUX, LIBPATH_LINUX, LIBS_LINUX  (Linux build)
#   INCLUDES_WIN,   LIBPATH_WIN,   LIBS_WIN    (Windows build)
#
# IMPORTANT: NEVER use raylib-windows/src (built for Windows/MinGW)
# in the Linux build, and vice versa. These are two different libraries,
# each built for a different platform.

heart-red_SRC            := main.c

# --- Linux config: uses the natively installed raylib (Linux) ---
heart-red_INCLUDES_LINUX :=
heart-red_LIBPATH_LINUX  :=
heart-red_LIBS_LINUX     := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11

# --- Windows config: uses raylib built for Windows/MinGW ---
heart-red_INCLUDES_WIN   := -I/home/le-glitch/raylib/raylib-windows/src
heart-red_LIBPATH_WIN    := -L/home/le-glitch/raylib/raylib-windows/src
heart-red_LIBS_WIN       := -lraylib -lopengl32 -lgdi32 -lwinmm -mwindows

heart-mult_SRC            := main.c

# --- Linux config: uses the natively installed raylib (Linux) ---
heart-mult_INCLUDES_LINUX :=
heart-mult_LIBPATH_LINUX  :=
heart-mult_LIBS_LINUX     := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11

# --- Windows config: uses raylib built for Windows/MinGW ---
heart-mult_INCLUDES_WIN   := -I/home/le-glitch/raylib/raylib-windows/src
heart-mult_LIBPATH_WIN    := -L/home/le-glitch/raylib/raylib-windows/src
heart-mult_LIBS_WIN       := -lraylib -lopengl32 -lgdi32 -lwinmm -mwindows

message_SRC            := main.c

# --- Linux config: uses the natively installed raylib (Linux) ---
message_INCLUDES_LINUX :=
message_LIBPATH_LINUX  :=
message_LIBS_LINUX     := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11

# --- Windows config: uses raylib built for Windows/MinGW ---
message_INCLUDES_WIN   := -I/home/le-glitch/raylib/raylib-windows/src
message_LIBPATH_WIN    := -L/home/le-glitch/raylib/raylib-windows/src
message_LIBS_WIN       := -lraylib -lopengl32 -lgdi32 -lwinmm -mwindows

love_SRC            := main.c

# --- Linux config: uses the natively installed raylib (Linux) ---
love_INCLUDES_LINUX :=
love_LIBPATH_LINUX  :=
love_LIBS_LINUX     := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11

# --- Windows config: uses raylib built for Windows/MinGW ---
love_INCLUDES_WIN   := -I/home/le-glitch/raylib/raylib-windows/src
love_LIBPATH_WIN    := -L/home/le-glitch/raylib/raylib-windows/src
love_LIBS_WIN       := -lraylib -lopengl32 -lgdi32 -lwinmm -mwindows

# Example for a future project WITHOUT raylib (template):
# otherproject_SRC        := main.c
# otherproject_LIBS_LINUX := -lm
# otherproject_LIBS_WIN   :=

# ==============================================================================
# Helpers to fetch either the project's value or the default value
# ==============================================================================
get_src            = $(if $($(1)_SRC),$($(1)_SRC),$(DEFAULT_SRC))
get_cc_linux       = $(if $($(1)_CC_LINUX),$($(1)_CC_LINUX),$(DEFAULT_CC_LINUX))
get_cc_win         = $(if $($(1)_CC_WIN),$($(1)_CC_WIN),$(DEFAULT_CC_WIN))
get_includes_linux = $(if $($(1)_INCLUDES_LINUX),$($(1)_INCLUDES_LINUX),$(DEFAULT_INCLUDES))
get_libpath_linux  = $(if $($(1)_LIBPATH_LINUX),$($(1)_LIBPATH_LINUX),$(DEFAULT_LIBPATH))
get_includes_win   = $(if $($(1)_INCLUDES_WIN),$($(1)_INCLUDES_WIN),$(DEFAULT_INCLUDES))
get_libpath_win    = $(if $($(1)_LIBPATH_WIN),$($(1)_LIBPATH_WIN),$(DEFAULT_LIBPATH))
get_libs_linux     = $(if $($(1)_LIBS_LINUX),$($(1)_LIBS_LINUX),$(DEFAULT_LIBS_LINUX))
get_libs_win       = $(if $($(1)_LIBS_WIN),$($(1)_LIBS_WIN),$(DEFAULT_LIBS_WIN))

# ==============================================================================
# Generic targets
# ==============================================================================

.PHONY: all
all: $(PROJECTS)

.PHONY: re
# Extra words typed after "re" (e.g. "make re heart-linux") are additional
# goals on the command line as far as make is concerned. We don't need to
# rebuild them ourselves: we just make "re" depend on "clean" so cleaning
# always happens first, then make builds the other requested goal(s)
# afterward using their own real, unmodified rules (no override, no warning).
RE_ARGS := $(filter-out re,$(MAKECMDGOALS))

ifeq ($(RE_ARGS),)
# No project given -> "make re" alone means "clean + rebuild everything"
re: clean
	@$(MAKE) --no-print-directory all
else
# A project (or project-linux / project-windows) was given as an extra
# goal -> just clean; make will build that goal right after, normally.
re: clean
endif

.PHONY: clean
clean:
	@for p in $(PROJECTS); do \
		rm -f $$p/game $$p/game.exe; \
	done
	@echo "Cleanup complete."

# ==============================================================================
# Pattern rule: automatically generated for each listed project
# ==============================================================================

# `make heart` -> builds Linux, then interactively asks about Windows.
# Everything happens inline in a single recipe: no separate -linux / -windows
# targets are exposed.
define PROJECT_RULE
.PHONY: $(1)
$(1):
	@echo "=== [$(1)] Linux build ==="
	$(call get_cc_linux,$(1)) $(1)/$(call get_src,$(1)) -o $(1)/game \
		$(WARN_FLAGS) \
		$(call get_includes_linux,$(1)) $(call get_libpath_linux,$(1)) $(call get_libs_linux,$(1))
	@echo "=== [$(1)] Linux build succeeded -> $(1)/game ==="
	@read -p ">> Also build '$(1)' for Windows? [y/N] " rep; \
	if [ "$$$$rep" = "y" ] || [ "$$$$rep" = "Y" ]; then \
		echo "=== [$(1)] Windows build ==="; \
		$(call get_cc_win,$(1)) $(1)/$(call get_src,$(1)) -o $(1)/game.exe \
			$(WARN_FLAGS) -mwindows -Wl,--subsystem,windows \
			$(call get_includes_win,$(1)) $(call get_libpath_win,$(1)) $(call get_libs_win,$(1)); \
		echo "=== [$(1)] Windows build succeeded -> $(1)/game.exe ==="; \
	else \
		echo ">> Windows build for '$(1)' cancelled."; \
	fi
endef

$(foreach p,$(PROJECTS),$(eval $(call PROJECT_RULE,$(p))))

# ==============================================================================
# Help
# ==============================================================================
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make                   -> build all projects (Linux, then interactively offers Windows)"
	@echo "  make re                -> clean + rebuild everything"
	@echo "  make re <project>      -> clean + rebuild only <project>  e.g. make re heart"
	@echo "  make <project>         -> build Linux, then interactively offer Windows  e.g. make heart"
	@echo "  make clean             -> remove all generated binaries"
	@echo ""
	@echo "Detected projects: $(PROJECTS)"
