cmake_minimum_required(VERSION 3.16)
project(game-of-life C)

set(CMAKE_C_STANDARD 11)

# ── Chercher raylib ───────────────────────────────────────────────────────────
find_package(raylib 4.0 QUIET)
if (NOT raylib_FOUND)
	include(FetchContent)
	FetchContent_Declare(
		raylib
		GIT_REPOSITORY	https://github.com/raysan5/raylib.git
		GIT_TAG			5.0
		GIT_SHALLOW		TRUE
	)
	set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
	FetchContent_MakeAvailable(raylib)
	target_compile_options(raylib PRIVATE -w)
endif()

# ── Sources ───────────────────────────────────────────────────────────────────
set(SOURCES
	src/app_draw-1.c
	src/app_draw-2.c
	src/app_draw-3.c
	src/app_draw-4.c
	src/app_init.c
	src/app_input-1.c
	src/app_input-2.c
	src/app_input-3.c
	src/app_input-4.c
	src/app_input-5.c
	src/app_input-6.c
	src/app_input-7.c
	src/app_input-8.c
	src/app_input-9.c
	src/app_map-1.c
	src/app_map-2.c
	src/app_map-3.c
	src/app_screens-1.c
	src/app_screens-2.c
	src/app_screens-3.c
	src/app_screens-4.c
	src/app_screens-5.c
	src/app_screens-6.c
	src/app_screens-7.c
	src/app_screens-8.c
	src/app_undo.c
	src/chunk_map-1.c
	src/chunk_map-2.c
	src/chunk_map-3.c
	src/chunk_map-4.c
	src/chunk.c
	src/config_io.c
	src/config_parse.c
	src/config.c
	src/main.c
	src/renderer_chunk.c
	src/renderer_coords.c
	src/renderer_draw.c
	src/renderer_grid.c
	src/renderer_theme-1.c
	src/renderer_theme-2.c
	src/save-1.c
	src/save-2.c
	src/save-3.c
	src/save-4.c
	src/save-5.c
	src/simulation-1.c
	src/simulation-2.c
	src/ui_browser-1.c
	src/ui_browser-2.c
	src/ui_browser-3.c
	src/ui_browser-4.c
	src/ui_browser-5.c
	src/ui_browser-6.c
	src/ui_browser-7.c
	src/ui_browser-8.c
	src/ui_browser-9.c
	src/ui_hud-1.c
	src/ui_hud-2.c
	src/ui_icons-1.c
	src/ui_icons-2.c
	src/ui_icons-3.c
	src/ui_icons-4.c
	src/ui_icons-5.c
	src/ui_keybinds-1.c
	src/ui_keybinds-2.c
	src/ui_keybinds-3.c
	src/ui_keybinds-4.c
	src/ui_menu-1.c
	src/ui_menu-2.c
	src/ui_random-1.c
	src/ui_random-2.c
	src/ui_savezone-1.c
	src/ui_savezone-2.c
	src/ui_savezone-3.c
	src/ui_savezone-4.c
	src/ui_savezone-5.c
	src/ui_toolbar-1.c
	src/ui_toolbar-2.c
	src/ui_toolbar-3.c
	src/ui_toolbar-4.c
	src/ui-1.c
	src/ui-2.c
	src/ui_colors-1.c
	src/ui_colors-2.c
	src/ui_colors-3.c
)

add_executable(game-of-life ${SOURCES})

target_include_directories(game-of-life PRIVATE src)
target_link_libraries(game-of-life PRIVATE raylib)

if (UNIX AND NOT APPLE)
	target_link_libraries(game-of-life PRIVATE m)
endif()

if (CMAKE_BUILD_TYPE STREQUAL "Release")
	target_compile_options(game-of-life PRIVATE -O2 -Wall -Wextra)
else()
	target_compile_options(game-of-life PRIVATE -O0 -g -Wall -Wextra)
endif()

set_target_properties(game-of-life PROPERTIES
	RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
)

message(STATUS "L'executable sera dans : ${CMAKE_SOURCE_DIR}/game-of-life")
message(STATUS "Lancez depuis la racine : ./game-of-life")
