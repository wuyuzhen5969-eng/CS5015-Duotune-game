"""Experiment: compare the basic DFS with propagation and fail-first variants.For every level and every configuration the solver is run REPEATS times; the table shows the median time and the (deterministic) search statistics.

python3 experiment.py           # the default levels
python3 experiment.py level_a.txt ...    # your own levels
"""
 
import os
import sys
import time
 
from check import Board
from solve import Solve
 
REPEATS = 5
 
DEFAULT_LEVELS = [
    "test_data/level1.txt",
    "test_data/level2.txt",
    "test_data/level3.txt",
    "test_data/hard-r3.txt",
    "test_data/hard-r4.txt",
    "test_data/hard-r5.txt",
    "test_data/hard-r6.txt",
]
 
CONFIGS = [
    ("basic", {}),
    ("propagation", {"use_propagation": True}),
    ("fail first", {"use_failfirst": True}),
    ("propagation + fail first",
     {"use_propagation": True, "use_failfirst": True}),
    ("fail first improved",
     {"use_failfirst": True, "improved_ff": True}),
    ("propagation + fail first improved",
     {"use_propagation": True, "use_failfirst": True, "improved_ff": True}),
]
 
RESULT_NAMES = {0: "no", 1: "unique", 2: "many"}
 
 
def solve_once(level, options):
    """Solve a level the way main() does; return (solver, seconds)."""
    start = time.perf_counter()
    solver = Solve(level, **options)
    alive = True
    if solver.use_propagation:
        seeds = [coord for coord, color in solver.state.items() if color != 0]
        alive = solver._propagate(seeds) is not None
    if alive:
        solver.search()
    return solver, time.perf_counter() - start
 
 
def measure(path, options):
    """Run REPEATS times; return the last solver and the median time in ms."""
    level = Board(path)
    times = []
    solver = None
    for _ in range(REPEATS):
        solver, seconds = solve_once(level, options)
        times.append(seconds)
    times.sort()
    return solver, times[len(times) // 2] * 1000
 
 
def print_table(rows):
    header = ("configuration", "time ms", "nodes", "backtracks",
              "forced", "ff checks")
    widths = [max(len(str(row[i])) for row in [header] + rows)
              for i in range(len(header))]
 
    def line(row):
        cells = [str(row[0]).ljust(widths[0])]
        cells += [str(value).rjust(width)
                  for value, width in zip(row[1:], widths[1:])]
        return "  ".join(cells)
 
    print(line(header))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(line(row))
    print("\n\n")
 
 
def run_level(path):
    level = Board(path)
    cells = len(level.axial)
    given = sum(1 for color in level.axial.values() if color != 0)
 
    rows, answers = [], []
    for name, options in CONFIGS:
        solver, milliseconds = measure(path, options)
        answers.append(solver.solutions) # type: ignore
        rows.append((name, f"{milliseconds:.2f}", solver.nodes, # type: ignore
                     solver.backtracks, solver.forced_count, # type: ignore
                     solver.failfirst_checks)) # type: ignore
 
    labels = {RESULT_NAMES[len(solutions)] for solutions in answers}
    agree = len(labels) == 1
    if agree and len(answers[0]) == 1:      # a unique solution must be identical
        agree = all(solutions == answers[0] for solutions in answers)
 
    print(f"\n{path}   radius {level.radius}, {cells} cells, {given} given\n")
    print_table(rows)
 
 
def main():
    paths = sys.argv[1:] or DEFAULT_LEVELS
    for path in paths:
        if os.path.exists(path):
            run_level(path)
        else:
            print(f"\n{path}: file not found, skipped")
 
 
if __name__ == "__main__":
    main()
