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
endif()

# ── Sources ───────────────────────────────────────────────────────────────────
set(SOURCES
	src/main.c
	src/app_init.c
	src/app_undo.c
	src/app_map.c
	src/app_map2.c
	src/app_input.c
	src/app_input7.c
	src/app_input2.c
	src/app_input3.c
	src/app_input8.c
	src/app_input4.c
	src/app_input5.c
	src/app_input6.c
	src/app_draw.c
	src/app_draw2.c
	src/app_draw3.c
	src/app_screens.c
	src/app_screens2.c
	src/app_screens3.c
	src/app_screens4.c
	src/app_screens5.c
	src/chunk_map.c
	src/chunk_map2.c
	src/chunk_map3.c
	src/chunk_map4.c
	src/simulation.c
	src/save.c
	src/save2.c
	src/save3.c
	src/ui.c
	src/ui_icons.c
	src/ui_icons2.c
	src/ui_icons3.c
	src/ui_icons5.c
	src/ui_icons4.c
	src/ui_toolbar.c
	src/ui_toolbar2.c
	src/ui_hud.c
	src/ui_menu.c
	src/ui_menu2.c
	src/ui_keybinds.c
	src/ui_keybinds2.c
	src/ui_keybinds3.c
	src/ui_savezone.c
	src/ui_savezone2.c
	src/ui_browser.c
	src/ui_browser2.c
	src/ui_random.c
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
