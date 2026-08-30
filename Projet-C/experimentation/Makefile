# ==============================================================================
# Generic multi-project Makefile
# ==============================================================================

SHELL := /bin/bash

# --- List of projects ---
PROJECTS := heart

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

heart_SRC            := main.c

# --- Linux config: uses the natively installed raylib (Linux) ---
heart_INCLUDES_LINUX :=
heart_LIBPATH_LINUX  :=
heart_LIBS_LINUX     := $(shell pkg-config --libs raylib 2>/dev/null || echo "-lraylib") -lm -lpthread -ldl -lrt -lX11

# --- Windows config: uses raylib built for Windows/MinGW ---
heart_INCLUDES_WIN   := -I/home/le-glitch/raylib/raylib-windows/src
heart_LIBPATH_WIN    := -L/home/le-glitch/raylib/raylib-windows/src
heart_LIBS_WIN       := -lraylib -lopengl32 -lgdi32 -lwinmm -mwindows


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
RE_ARGS := $(filter-out re,$(MAKECMDGOALS))

ifeq ($(RE_ARGS),)
re: clean
	@$(MAKE) --no-print-directory all
else
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
