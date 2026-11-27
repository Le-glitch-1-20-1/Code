#!/usr/bin/env python3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import argparse
import os
import random
import sys
import time
import numpy as np

# ============================================================================
# DISPLAY
# By default the script only uses print() and input() (ConsoleDisplay class).
# If the file "display_layer.py" is next to the script, it is loaded
# automatically and adds a display layer (colours, menus, bars...).
# To prevent it from loading:
#   - run the script with the  --no-ui  option
#   - or set the environment variable  PROJECT_NO_UI=1
#   - or set ACTIVE = False in display_layer.py (or delete the file)
#
# LANGUAGE
# Messages are in English by default. To get them in French, the file
# "lang_fr.json" must be next to the script, then:
#   - run the script with  --lang fr
#   - or set the environment variable  PROJECT_LANG=fr
# ============================================================================

import json
import re

_LINE_OPEN: list[bool] = [False]


def _pick_language() -> str:
	# Read (and remove) --lang xx / --lang=xx from the command line, then PROJECT_LANG
	lang: str = os.environ.get("PROJECT_LANG", "en").strip().lower() or "en"
	args: list[str] = sys.argv
	i: int = 1
	while i < len(args):
		if args[i] == "--lang" and i + 1 < len(args):
			lang = args[i + 1].strip().lower()
			del args[i:i + 2]
			continue
		if args[i].startswith("--lang="):
			lang = args[i].split("=", 1)[1].strip().lower()
			del args[i]
			continue
		i += 1
	return lang


class _Translator:
	# Translates English messages using lang_<code>.json; returns the text unchanged otherwise
	def __init__(self, lang: str) -> None:
		self.lang: str = "en"
		self.exact: dict[str, str] = {}
		self.patterns: list[tuple[re.Pattern[str], list]] = []
		if lang == "en":
			return
		path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"lang_{lang}.json")
		try:
			with open(path, encoding="utf-8") as handle:
				data: dict = json.load(handle)
		except (OSError, ValueError):
			return
		self.lang = lang
		self.exact = data.get("exact", {})
		for source, target in data.get("patterns", []):
			literal: str = "".join(p for p in source if isinstance(p, str))
			if len(literal.strip()) < 3:
				continue
			regex: str = "".join(re.escape(p) if isinstance(p, str) else f"(?P<p{p}>.*?)" for p in source)
			self.patterns.append((re.compile(regex + r"\Z", re.DOTALL), target, len(literal)))
		self.patterns.sort(key=lambda item: -item[2])

	def __call__(self, text: object) -> object:
		if self.lang == "en" or not isinstance(text, str) or not text:
			return text
		found: str | None = self._lookup(text)
		if found is not None:
			return found
		if "\n" in text:
			return "\n".join(self._lookup(row) or row for row in text.split("\n"))
		return text

	def _exact(self, text: str) -> str | None:
		if text in self.exact:
			return self.exact[text]
		stripped: str = text.strip()
		if stripped and stripped != text and stripped in self.exact:
			start: int = text.index(stripped)
			return text[:start] + self.exact[stripped] + text[start + len(stripped):]
		return None

	def _lookup(self, text: str) -> str | None:
		found: str | None = self._exact(text)
		if found is not None:
			return found
		for regex, target, _ in self.patterns:
			match = regex.match(text)
			if match:
				values: dict[str, str] = match.groupdict()
				# Inserted values (e.g. a "[DRY RUN] " prefix) are translated too if known
				return "".join(p if isinstance(p, str) else (self._exact(values.get(f"p{p}", "")) or values.get(f"p{p}", "")) for p in target)
		return None


tr: _Translator = _Translator(_pick_language())


def _translate_argparse() -> None:
	# Translate the help texts given to argparse (descriptions, options, epilogs)
	if tr.lang == "en":
		return
	import argparse
	original_init = argparse.ArgumentParser.__init__
	original_add = argparse._ActionsContainer.add_argument
	original_group = argparse._ActionsContainer.add_argument_group

	def init(self, *args, **kwargs):
		for key in ("description", "epilog"):
			if key in kwargs:
				kwargs[key] = tr(kwargs[key])
		original_init(self, *args, **kwargs)

	def add_argument(self, *args, **kwargs):
		if "help" in kwargs:
			kwargs["help"] = tr(kwargs["help"])
		return original_add(self, *args, **kwargs)

	def add_argument_group(self, *args, **kwargs):
		args = tuple(tr(a) for a in args)
		if "description" in kwargs:
			kwargs["description"] = tr(kwargs["description"])
		return original_group(self, *args, **kwargs)

	argparse.ArgumentParser.__init__ = init
	argparse._ActionsContainer.add_argument = add_argument
	argparse._ActionsContainer.add_argument_group = add_argument_group
	original_parser = argparse._SubParsersAction.add_parser

	def add_parser(self, name, **kwargs):
		if "help" in kwargs:
			kwargs["help"] = tr(kwargs["help"])
		return original_parser(self, name, **kwargs)

	argparse._SubParsersAction.add_parser = add_parser


_translate_argparse()


def _write(*args: object, **kwargs: object) -> None:
	# print() that first breaks the line if a progress bar is using the current line
	if _LINE_OPEN[0]:
		print()
		_LINE_OPEN[0] = False
	print(*args, **kwargs)


def _input(prompt: str) -> str:
	# input() that first breaks the line if a progress bar is using the current line
	if _LINE_OPEN[0]:
		print()
		_LINE_OPEN[0] = False
	return input(prompt)


class _ConsoleProgress:
	# Simple text progress bar (a single line rewritten with \r)
	def __init__(self, total: float | None, description: str = "") -> None:
		self.total: float | None = total
		self.done: float = 0
		self.description: str = tr(description)
		self._last: int = -1
		self._length: int = 0

	def __enter__(self) -> "_ConsoleProgress":
		self._display(force=True)
		return self

	def __exit__(self, *exc: object) -> None:
		self._display(force=True)
		print()
		_LINE_OPEN[0] = False

	def advance(self, n: float = 1, description: str | None = None) -> None:
		self.done += n
		if description is not None:
			self.description = tr(description)
		self._display()

	def set_value(self, done: float | None = None, total: float | None = None, description: str | None = None) -> None:
		if done is not None:
			self.done = done
		if total is not None:
			self.total = total
		if description is not None:
			self.description = tr(description)
		self._display()

	def _display(self, force: bool = False) -> None:
		if self.total:
			percent: int = int(min(self.done, self.total) * 100 / self.total)
			if percent == self._last and not force:
				return
			self._last = percent
			row: str = f"{self.description} : {percent:3d}% ({int(self.done)}/{int(self.total)})"
		else:
			row = f"{self.description} : {int(self.done)}"
		# The spaces erase what is left of a longer previous line
		if not _LINE_OPEN[0]:
			self._length = 0
		print("\r" + row.ljust(self._length), end="", flush=True)
		self._length = len(row)
		_LINE_OPEN[0] = True


class _ConsoleMultiProgress:
	# Several tasks tracked at once, shown on a single line
	def __init__(self, tasks: list[tuple[str, float]]) -> None:
		self.tasks: list[list] = [[tr(name), float(total), 0.0] for name, total in tasks]

	def __enter__(self) -> "_ConsoleMultiProgress":
		return self

	def __exit__(self, *exc: object) -> None:
		self._display()
		print()
		_LINE_OPEN[0] = False

	def advance(self, index: int, n: float = 1) -> None:
		task: list = self.tasks[index]
		task[2] = min(task[1], task[2] + n)
		self._display()

	def finished(self) -> bool:
		return all(t[2] >= t[1] for t in self.tasks)

	def _display(self) -> None:
		pieces: list[str] = [f"{name} {int(done * 100 / total) if total else 100:3d}%" for name, total, done in self.tasks]
		print("\r" + " | ".join(pieces), end="", flush=True)
		_LINE_OPEN[0] = True


class _ConsoleStatus:
	# "In progress..." message shown before a long operation
	def __init__(self, message: str) -> None:
		self.message: str = tr(message)

	def __enter__(self) -> "_ConsoleStatus":
		_write(f"{self.message} ...", flush=True)
		return self

	def __exit__(self, *exc: object) -> None:
		pass

	def update(self, message: str) -> None:
		_write(f"{tr(message)} ...", flush=True)


class ConsoleDisplay:
	# Minimal display: only _write() and _input(), no dependency
	def __init__(self) -> None:
		self.tr: _Translator = tr
		self.lang: str = tr.lang

	def clear(self) -> None:
		_write()

	def banner(self, title: str, subtitle: str = "") -> None:
		title, subtitle = tr(title), tr(subtitle)
		width: int = max(len(title), len(subtitle)) + 4
		_write("=" * width)
		_write(f"  {title}")
		if subtitle:
			_write(f"  {subtitle}")
		_write("=" * width)
		_write()

	def section(self, title: str) -> None:
		_write()
		_write(f"--- {tr(title)} ---")

	def info(self, message: str = "") -> None:
		_write(tr(message))

	def muted(self, message: str) -> None:
		_write(tr(message))

	def success(self, message: str) -> None:
		_write(f"[OK] {tr(message)}")

	def warning(self, message: str) -> None:
		_write(f"{tr('[WARNING]')} {tr(message)}")

	def error(self, message: str) -> None:
		_write(f"{tr('[ERROR]')} {tr(message)}", file=sys.stderr)

	def block(self, text: str, title: str | None = None) -> None:
		# Framed text (equivalent of a panel)
		if title:
			_write(f"[{tr(title)}]")
		_write(tr(text))
		_write()

	def key_values(self, pairs: list[tuple[str, object]], title: str | None = None) -> None:
		# Aligned "key: value" list
		if title:
			_write(f"[{tr(title)}]")
		pairs = [(tr(str(key)), tr(value)) for key, value in pairs]
		width: int = max((len(key) for key, _ in pairs), default=0)
		for key, value in pairs:
			_write(f"  {key:<{width}} : {value}")
		_write()

	def table(self, columns: list[str], rows: list[list[object]], title: str | None = None) -> None:
		# Text table with aligned columns
		columns = [tr(str(c)) for c in columns]
		cells: list[list[str]] = [[str(tr(c)) for c in row] for row in rows]
		widths: list[int] = [len(c) for c in columns]
		for row in cells:
			for i, c in enumerate(row):
				if i < len(widths):
					widths[i] = max(widths[i], len(c))
		if title:
			_write(tr(title))
		_write(" | ".join(c.ljust(widths[i]) for i, c in enumerate(columns)))
		_write("-+-".join("-" * w for w in widths))
		for row in cells:
			_write(" | ".join(c.ljust(widths[i]) if i < len(widths) else c for i, c in enumerate(row)))
		_write()

	def tree(self, root: str, children: list) -> None:
		# children: list of str or of (name, sub_children) tuples
		_write(tr(root))
		self._tree(children, "")

	def _tree(self, children: list, prefix: str) -> None:
		for i, child in enumerate(children):
			last: bool = i == len(children) - 1
			name: str = child[0] if isinstance(child, tuple) else str(child)
			_write(f"{prefix}{'`-- ' if last else '|-- '}{tr(name)}")
			if isinstance(child, tuple):
				self._tree(child[1], prefix + ("    " if last else "|   "))

	def code(self, text: str, language: str = "", title: str | None = None) -> None:
		if title:
			_write(f"[{tr(title)}]")
		for number, row in enumerate(text.splitlines(), 1):
			_write(f"{number:3d} | {row}")
		_write()

	def markdown(self, text: str) -> None:
		_write(tr(text))
		_write()

	def log(self, level: str, message: str) -> None:
		_write(f"[{time.strftime('%H:%M:%S')}] {level:<8} {tr(message)}")

	def ask(self, question: str, default: str | None = None) -> str | None:
		# Returns None if the user cancels (Ctrl+C / Ctrl+D)
		suffix: str = f" [{default}]" if default else ""
		try:
			answer: str = _input(f"{tr(question)}{suffix} : ").strip()
		except (EOFError, KeyboardInterrupt):
			_write()
			return None
		return answer if answer else (default if default is not None else "")

	def ask_path(self, question: str, default: str | None = None) -> str | None:
		return self.ask(question, default)

	def ask_number(self, question: str, default: float | None = None, integer: bool = True, minimum: float | None = None, maximum: float | None = None) -> float | int | None:
		# Ask again until the input is a valid number
		while True:
			raw_value: str | None = self.ask(question, None if default is None else str(default))
			if raw_value is None:
				return None
			try:
				value: float | int = int(raw_value) if integer else float(raw_value)
			except ValueError:
				_write(tr("  Invalid value, try again."))
				continue
			if minimum is not None and value < minimum:
				_write(tr(f"  Value must be >= {minimum}."))
				continue
			if maximum is not None and value > maximum:
				_write(tr(f"  Value must be <= {maximum}."))
				continue
			return value

	def confirm(self, question: str, default: bool = False) -> bool | None:
		hint: str = tr("Y/n") if default else tr("y/N")
		while True:
			try:
				answer: str = _input(f"{tr(question)} ({hint}) : ").strip().lower()
			except (EOFError, KeyboardInterrupt):
				_write()
				return None
			if not answer:
				return default
			if answer in ("y", "yes", "o", "oui"):
				return True
			if answer in ("n", "no", "non"):
				return False
			_write(tr("  Answer y or n."))

	def choose(self, question: str, options: list[str], default: str | None = None) -> str | None:
		# Numbered menu; returns the chosen option (untranslated) or None if cancelled
		if not options:
			return None
		_write(tr(question))
		for i, option in enumerate(options, 1):
			_write(f"  {i}. {tr(option)}")
		default_index: int | None = options.index(default) + 1 if default in options else None
		while True:
			try:
				raw_value: str = _input(tr(f"Your choice (1-{len(options)})") + (f" [{default_index}]" if default_index else "") + " : ").strip()
			except (EOFError, KeyboardInterrupt):
				_write()
				return None
			if not raw_value and default_index:
				return options[default_index - 1]
			if raw_value.isdigit() and 1 <= int(raw_value) <= len(options):
				return options[int(raw_value) - 1]
			_write(tr("  Invalid choice."))

	def choose_many(self, question: str, options: list[str], checked: list[str] | None = None) -> list[str] | None:
		# Multiple selection: comma-separated numbers
		_write(tr(question))
		for i, option in enumerate(options, 1):
			mark: str = "*" if checked and option in checked else " "
			_write(f"  {i}. [{mark}] {tr(option)}")
		while True:
			try:
				raw_value: str = _input(tr("Comma-separated numbers (empty = default selection, 'all' = everything): ")).strip().lower()
			except (EOFError, KeyboardInterrupt):
				_write()
				return None
			if not raw_value:
				return list(checked or [])
			if raw_value in ("all", "tout", "*"):
				return list(options)
			try:
				indices: list[int] = [int(x) for x in raw_value.replace(" ", "").split(",") if x]
			except ValueError:
				_write(tr("  Invalid input."))
				continue
			if all(1 <= i <= len(options) for i in indices):
				return [options[i - 1] for i in dict.fromkeys(indices)]
			_write(tr("  Number out of range."))

	def pause(self, message: str = "Press Enter to continue...") -> None:
		try:
			_input(f"\n{tr(message)}")
		except (EOFError, KeyboardInterrupt):
			_write()

	def progress(self, total: float | None, description: str = "") -> _ConsoleProgress:
		return _ConsoleProgress(total, description)

	def multi_progress(self, tasks: list[tuple[str, float]]) -> _ConsoleMultiProgress:
		return _ConsoleMultiProgress(tasks)

	def status(self, message: str) -> _ConsoleStatus:
		return _ConsoleStatus(message)


def load_display() -> ConsoleDisplay:
	# Load the optional display layer (display_layer.py) if it is present and allowed
	simple_console: ConsoleDisplay = ConsoleDisplay()
	if "--no-ui" in sys.argv:
		sys.argv.remove("--no-ui")
		return simple_console
	if os.environ.get("PROJECT_NO_UI", "").strip() not in ("", "0"):
		return simple_console
	folder: str = os.path.dirname(os.path.abspath(__file__))
	if folder not in sys.path:
		sys.path.insert(0, folder)
	if not os.path.isfile(os.path.join(folder, "display_layer.py")):
		return simple_console
	try:
		import display_layer
		return display_layer.create_display(simple_console) or simple_console
	except Exception as exc:
		# The layer is present but could not start: say why, then use the plain console
		missing: str | None = getattr(exc, "name", None) if isinstance(exc, ImportError) else None
		if missing:
			simple_console.muted(tr(f"display_layer.py not loaded: the '{missing}' module is missing (pip install rich questionary)."))
		else:
			simple_console.muted(tr(f"display_layer.py not loaded: {exc}"))
		simple_console.muted(tr("Plain console display used (add --no-ui to hide this message)."))
		return simple_console


ui: ConsoleDisplay = load_display()
# ============================================================================


@dataclass
class City:
	# Represents a city by its identifier and Cartesian coordinates
	identifier: int
	x: float
	y: float


class TSPGraph:
	# Holds the Euclidean distances and the pheromone matrix between every pair of cities
	def __init__(self, cities: list[City]) -> None:
		self.cities: list[City] = cities
		self.city_count: int = len(cities)
		self.distances: np.ndarray = self._compute_distances()
		self.pheromones: np.ndarray = np.ones((self.city_count, self.city_count))

	def _compute_distances(self) -> np.ndarray:
		# Build the symmetric matrix of Euclidean distances between every city
		matrix: np.ndarray = np.zeros((self.city_count, self.city_count))
		for i in range(self.city_count):
			for j in range(self.city_count):
				dx: float = self.cities[i].x - self.cities[j].x
				dy: float = self.cities[i].y - self.cities[j].y
				matrix[i][j] = (dx ** 2 + dy ** 2) ** 0.5
		return matrix

	def tour_length(self, tour: list[int]) -> float:
		# Compute the total length of a closed tour through every city
		total: float = 0.0
		for index_value in range(len(tour)):
			current_city: int = tour[index_value]
			next_city: int = tour[(index_value + 1) % len(tour)]
			total += self.distances[current_city][next_city]
		return total


class CitySelectionStrategy(ABC):
	# Abstract interface defining how an ant chooses its next city
	@abstractmethod
	def choose_next_city(self, graph: TSPGraph, current_city: int, unvisited_cities: list[int], alpha: float, beta: float) -> int:
		raise NotImplementedError


class ProbabilisticStrategy(CitySelectionStrategy):
	# Implement the classic probabilistic ACO rule based on pheromones and visibility
	def choose_next_city(self, graph: TSPGraph, current_city: int, unvisited_cities: list[int], alpha: float, beta: float) -> int:
		weights: list[float] = []
		for candidate_city in unvisited_cities:
			pheromone: float = graph.pheromones[current_city][candidate_city] ** alpha
			distance: float = graph.distances[current_city][candidate_city]
			visibility: float = (1.0 / distance) ** beta if distance > 0 else 0.0
			weights.append(pheromone * visibility)
		total_weight: float = sum(weights)
		if total_weight == 0:
			return random.choice(unvisited_cities)
		probabilities: list[float] = [individual_weight / total_weight for individual_weight in weights]
		return random.choices(unvisited_cities, weights=probabilities, k=1)[0]


@dataclass
class Ant:
	# Represents an ant making a full tour of the graph
	tour: list[int] = field(default_factory=list)
	length: float = 0.0

	def reset(self, start_city: int) -> None:
		# Reset the ant for a new iteration starting from a given city
		self.tour = [start_city]
		self.length = 0.0

	def build_tour(self, graph: TSPGraph, strategy: CitySelectionStrategy, alpha: float, beta: float) -> None:
		# Make the ant visit every city one by one following the given strategy
		unvisited_cities: list[int] = [city.identifier for city in graph.cities if city.identifier != self.tour[0]]
		while unvisited_cities:
			current_city: int = self.tour[-1]
			next_city: int = strategy.choose_next_city(graph, current_city, unvisited_cities, alpha, beta)
			self.tour.append(next_city)
			unvisited_cities.remove(next_city)
		self.length = graph.tour_length(self.tour)


class ACOColony:
	# Orchestrate every iteration of the ant colony algorithm
	def __init__(self, graph: TSPGraph, ant_count: int, alpha: float, beta: float, evaporation: float, iterations: int) -> None:
		self.graph: TSPGraph = graph
		self.ant_count: int = ant_count
		self.alpha: float = alpha
		self.beta: float = beta
		self.evaporation: float = evaporation
		self.iterations: int = iterations
		self.strategy: CitySelectionStrategy = ProbabilisticStrategy()
		self.best_tour: Optional[list[int]] = None
		self.best_length: float = float("inf")
		self.length_history: list[float] = []

	def _deposit_pheromones(self, ants: list[Ant]) -> None:
		# Evaporate the existing pheromones then lay new trails according to tour quality
		self.graph.pheromones *= (1.0 - self.evaporation)
		for ant in ants:
			deposit: float = 1.0 / ant.length
			for index_value in range(len(ant.tour)):
				current_city: int = ant.tour[index_value]
				next_city: int = ant.tour[(index_value + 1) % len(ant.tour)]
				self.graph.pheromones[current_city][next_city] += deposit
				self.graph.pheromones[next_city][current_city] += deposit

	def run_iteration(self) -> list[Ant]:
		# Run one full iteration: every ant builds a tour, then the pheromones are updated
		ants: list[Ant] = []
		for _ in range(self.ant_count):
			ant: Ant = Ant()
			start_city: int = random.randint(0, self.graph.city_count - 1)
			ant.reset(start_city)
			ant.build_tour(self.graph, self.strategy, self.alpha, self.beta)
			ants.append(ant)
			if ant.length < self.best_length:
				self.best_length = ant.length
				self.best_tour = ant.tour.copy()
		self._deposit_pheromones(ants)
		self.length_history.append(self.best_length)
		return ants


def run_console(colony: ACOColony) -> None:
	# Run every iteration while showing progress and improvements
	with ui.progress(colony.iterations, "Iterations") as bar:
		for _ in range(colony.iterations):
			colony.run_iteration()
			bar.advance(1, f"Iterations (best length {colony.best_length:.2f})")


def run(colony: ACOColony) -> None:
	# Use the display layer animation if it exists, otherwise the console
	visualize = getattr(ui, "visualize_aco", None)
	if visualize is not None:
		try:
			visualize(colony)
			return
		except ImportError:
			pass
	run_console(colony)


def generate_random_cities(number: int, width: float, height: float) -> list[City]:
	# Generate a set of cities with random coordinates in a rectangular area
	return [City(identifier=i, x=random.uniform(0, width), y=random.uniform(0, height)) for i in range(number)]


def build_parser() -> argparse.ArgumentParser:
	# Build the command-line argument parser with every tunable parameter
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Solving the TSP with ant colony optimisation (ACO)")
	parser.add_argument("--cities", type=int, default=25, help="Number of randomly generated cities")
	parser.add_argument("--ants", type=int, default=30, help="Number of ants per iteration")
	parser.add_argument("--alpha", type=float, default=1.0, help="Weight of the pheromone influence")
	parser.add_argument("--beta", type=float, default=3.0, help="Weight of the visibility influence (1/distance)")
	parser.add_argument("--evaporation", type=float, default=0.5, help="Pheromone evaporation rate (0 to 1)")
	parser.add_argument("--iterations", type=int, default=100, help="Number of algorithm iterations")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py)")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	parser.add_argument("--seed", type=int, default=None, help="Random seed to reproduce a result")
	return parser


def interactive_menu() -> argparse.Namespace:
	# Offer a console menu with every parameter available from the CLI
	ui.banner("ACO-TSP", "Travelling salesman by ant colony")
	cities = ui.ask_number("Number of cities", 25, minimum=2)
	ants = ui.ask_number("Number of ants", 30, minimum=1)
	alpha = ui.ask_number("Alpha (pheromone weight)", 1.0, integer=False)
	beta = ui.ask_number("Beta (visibility weight)", 3.0, integer=False)
	evaporation = ui.ask_number("Evaporation rate", 0.5, integer=False, minimum=0, maximum=1)
	iterations = ui.ask_number("Number of iterations", 100, minimum=1)
	if None in (cities, ants, alpha, beta, evaporation, iterations):
		sys.exit(0)
	seed_input: str = ui.ask("Random seed (empty for random)") or ""
	seed: Optional[int] = int(seed_input) if seed_input.lstrip("-").isdigit() else None
	return argparse.Namespace(cities=cities, ants=ants, alpha=alpha, beta=beta, evaporation=evaporation, iterations=iterations, seed=seed)


def main() -> None:
	parser: argparse.ArgumentParser = build_parser()
	if len(sys.argv) > 1:
		arguments: argparse.Namespace = parser.parse_args()
	else:
		arguments = interactive_menu()
	if arguments.seed is not None:
		random.seed(arguments.seed)
	cities: list[City] = generate_random_cities(arguments.cities, 100.0, 100.0)
	graph: TSPGraph = TSPGraph(cities)
	colony: ACOColony = ACOColony(graph, arguments.ants, arguments.alpha, arguments.beta, arguments.evaporation, arguments.iterations)
	run(colony)
	ui.success(f"Best length found: {colony.best_length:.2f}")
	ui.info(f"Best tour: {colony.best_tour}")


if __name__ == "__main__":
	main()
