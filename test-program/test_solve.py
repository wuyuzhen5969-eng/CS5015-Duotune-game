
"""Unit and integration tests for the Duotone solver."""

import unittest
import os
import tempfile

from check import Board, Check
from solve import Solve

# The solution of test_data/level1.txt
SOLUTION1_LIST = [
    [1, 2, 2],
    [2, 2, 1, 1],
    [2, 1, 1, 2, 2],
    [1, 2, 2, 1],
    [2, 1, 1],
]
SOLUTION1_PRINT =  """2
  1 2 2
 2 2 1 1
2 1 1 2 2
 1 2 2 1
  2 1 1"""


#helper
def state_to_rows(radius: int, state: dict) -> list:
    """Turn a {(q, r): color} dict into rows (top to bottom, left to right)."""
    rows = []
    for q in range(-radius, radius + 1):
        cells = sorted((r, c) for (qq, r), c in state.items() if qq == q)
        rows.append([c for _, c in cells])
    return rows

def blank(solver: Solve) -> Solve:
    """Wipe givens and counts, so a test can set up its own position."""
    for coord in solver.state:
        solver.state[coord] = 0
    solver.count = [[0, 0] for _ in solver.line_list]
    return solver

def state_to_board(radius: int, state: dict) -> Board:
    """Write a {(q, r): color} dict to a temp file and read it back as a Board."""
    rows = state_to_rows(radius, state)
    text = str(radius) + "\n" + "\n".join(" ".join(map(str, r)) for r in rows)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
        path = f.name
    try:
        return Board(path)
    finally:
        os.remove(path)


class TestSolve(unittest.TestCase):
    """Test the solver."""

    def setUp(self):
        self.level0_empty = Board("test_data/level0-empty.txt")
        self.level_small_many = Board("test_data/level-small-many.txt")
        self.level1 = Board("test_data/level1.txt")
        self.level1_many = Board("test_data/level1-many.txt")
        self.level1_nosolution = Board("test_data/level1-nosolution.txt")
        self.solution1 =Board("test_data/solution1.txt")
        self.level3 = Board("test_data/level3.txt")
        self.empty_radius1 = Board("test_data/empty-radius1.txt")
        self.solver_small_many = Solve(self.level_small_many)
        self.solver0_empty = Solve(self.level0_empty)
        self.solver1 = Solve(self.level1)
        self.solver1_many = Solve(self.level1_many)
        self.solver1_nosolution = Solve(self.level1_nosolution)
        self.solver3 = Solve(self.level3)
        self.solver_empty_radius1 = Solve(self.empty_radius1)
        self.solver_solution1 = Solve(self.solution1)
    
    def test_init(self):
        """Test the preprocessing done by Solve.__init__."""
        # state is an independent copy of the level
        before = dict(self.level1.axial)
        self.solver1.state[(0, 0)] = 2
        self.assertIsNot(self.solver1.state, self.level1.axial)
        self.assertEqual(self.level1.axial, before)
 
        # the empty list holds exactly the cells that are 0 in the level
        self.assertEqual(len(self.solver1.empty), 8)
 
    def test_init_empty_cells(self):
        """`empty` is exactly the set of 0-cells, without duplicates."""
        expected = {c for c, v in self.level1.axial.items() if v == 0}
        self.assertEqual(set(self.solver1.empty), expected)
        self.assertEqual(len(self.solver1.empty), len(set(self.solver1.empty)))
        self.assertEqual(len(self.solver3.empty), sum(v == 0 for v in self.level3.axial.values()))

    def test_init_attributes(self):
        """Defaults: radius, colors, counters, solutions and flags."""
        solver = self.solver1
        self.assertEqual(solver.radius, 2)
        self.assertEqual(self.solver3.radius, 3)
        self.assertEqual(solver.color, [1, 2])
        self.assertEqual((solver.nodes, solver.backtracks), (0, 0))
        self.assertEqual(solver.solutions, [])
        self.assertFalse(solver.use_propagation)
        self.assertFalse(solver.use_failfirst)

    def test_build_line(self):
        """Test line_list are lines in each of 3 directions, which do not hold state colors."""
        self.assertEqual(len(self.solver1.line_list), 15)
        self.assertEqual(len(self.solver3.line_list), 21)
        for line in self.solver1.line_list:
            for item in line:
                self.assertIn(item, self.level1.axial)
                self.assertIsInstance(item, tuple)   # a coordinate, not a color
                self.assertEqual(len(item), 2)
        
    def test_build_line_lengths(self):
        """Every direction has lines of length r+1 .. 2r+1 .. r+1."""
        for solver, radius in ((self.solver1, 2), (self.solver3, 3)):
            n = 2 * radius + 1
            lengths = [len(line) for line in solver.line_list]
            expected = [n - abs(k - radius) for k in range(n)]
            self.assertEqual(lengths, expected * 3)

    def test_cell_lines(self):
        """Each cell is on exactly 3 lines, at the recorded index."""
        for coord, entries in self.solver1.cell_lines.items():
            self.assertEqual(len(entries), 3)
            for index, lid in entries:
                self.assertEqual(self.solver1.line_list[lid][index], coord)

    def test_count(self):
        """Test initial counts of given gold and blue cells."""
        for solver, level in ((self.solver1, self.level1),
                              (self.solver3, self.level3)):
            for lid, line in enumerate(solver.line_list):
                gold = sum(1 for c in line if level.axial[c] == 1)
                blue = sum(1 for c in line if level.axial[c] == 2)
                self.assertEqual(solver.count[lid], [gold, blue])
        self.assertEqual(self.solver0_empty.count, [[0, 0]] * 3)

    def test_bound(self):
        """Bound of a line is ceil(length / 2)."""
        for lid, line in enumerate(self.solver1.line_list):
            self.assertEqual(self.solver1.bound[lid], (len(line) + 1) // 2)
        for lid, line in enumerate(self.solver3.line_list):
            self.assertEqual(self.solver3.bound[lid], (len(line) + 1) // 2)
        self.assertEqual(self.solver1.bound[:5], [2, 2, 3, 2, 2])
        self.assertEqual(self.solver3.bound[:7], [2, 3, 3, 4, 3, 3, 2])
        self.assertEqual(self.solver0_empty.bound, [1, 1, 1])


    def test_place_remove(self):
        """Test that _place and _remove keep state, counts."""
        solver = self.solver1
        original_state = dict(solver.state)
        original_counts = [row[:] for row in solver.count]
 
        solver._place((0, 1), 2)
        self.assertEqual(solver.state[(0, 1)], 2)
        self.assertNotEqual(solver.count, original_counts)
 
        solver._remove((0, 1))
        self.assertEqual(solver.state, original_state)
        self.assertEqual(solver.count, original_counts)

    def test_place_updates_exactly_the_three_lines(self):
        """_place adds 1 to the right color on the 3 lines of the cell only."""
        solver = self.solver1
        before = [row[:] for row in solver.count]
        on_lines = {lid for _, lid in solver.cell_lines[(0, 1)]}
 
        solver._place((0, 1), 2)           # blue -> index 1
        for lid, (gold, blue) in enumerate(solver.count):
            if lid in on_lines:
                self.assertEqual([gold, blue], [before[lid][0], before[lid][1] + 1])
            else:
                self.assertEqual([gold, blue], before[lid])
 
        solver._remove((0, 1))
        solver._place((0, 1), 1)           # gold -> index 0
        for lid in on_lines:
            self.assertEqual(solver.count[lid][0], before[lid][0] + 1)
            self.assertEqual(solver.count[lid][1], before[lid][1])

    def test_remove_uses_the_placed_color(self):
        """_remove decrements the color that is on the cell."""
        solver = self.solver1
        original = [row[:] for row in solver.count]
        solver._place((0, 1), 1)
        solver._place((0, 2), 2)
        solver._remove((0, 1))
        solver._remove((0, 2))
        self.assertEqual(solver.count, original)
        self.assertEqual(solver.state[(0, 1)], 0)
        self.assertEqual(solver.state[(0, 2)], 0)

    def test_check_no_three(self):
        """ Solve._check_no_three for different situations"""
        #Placing 1 at (0,1) makes `1 1 1` in the middle row of level1.
        self.solver1._place((0, 1), 1)
        self.assertFalse(self.solver1._check_no_three((0, 1)))
        self.solver1._remove((0, 1))

        # Placing 2 at (0,1) gives `2 1 1 2 0` -> no triple.
        self.solver1._place((0, 1), 2)
        self.assertTrue(self.solver1._check_no_three((0, 1)))

        # Three empty (0) cells in a row are not a violation.
        solver = blank(self.solver1)
        for coord in solver.state:
            self.assertTrue(solver._check_no_three(coord))

        #Lines shorter than 3 cannot contain a triple (radius 1 has such).
        solver = blank(self.solver_small_many)
        for coord in solver.state:
            solver.state[coord] = 1
        # on radius 1 only the 3-cell lines can fail
        for coord in solver.state:
            solver._check_no_three(coord)
        self.assertFalse(solver._check_no_three((0, 0)))

    def test_check_balance(self):
        """ Solve._check_balance for different situations"""
        #Initial counts of a valid level never exceed the bound.
        for coord in self.solver1.state:
            self.assertTrue(self.solver1._check_balance(coord))
        for coord in self.solver3.state:
            self.assertTrue(self.solver3._check_balance(coord))

        #gold over bound
        solver = blank(self.solver1)
        coord = (0, 0)
        lid = solver.cell_lines[coord][2][1]
        solver.count[lid] = [0, solver.bound[lid] + 1]
        self.assertFalse(solver._check_balance(coord))

    def test_basice_search(self):
        """Test the basic DFS ."""
        self.solver1.search()
        self.assertEqual(len(self.solver1.solutions), 1)
        self.assertEqual(state_to_rows(2, self.solver1.solutions[0]), SOLUTION1_LIST)

        solver = self.solver1_many
        solver.search()
        self.assertEqual(len(solver.solutions), 2)
        first, second = solver.solutions
        self.assertNotEqual(first, second)

        solver = self.solver1_nosolution
        solver.search()
        self.assertEqual(solver.solutions, [])
        self.assertGreater(solver.backtracks, 0)

    def test_force_color(self):
        """Test Solve._force_color"""
        solver = self.solver1
        self.assertEqual(solver._force_color((-2, 0), 1), "placed")
        self.assertIsNone(solver._force_color((0, -1), 2))
        state_before = dict(solver.state)
        count_before = [row[:] for row in solver.count]
        self.assertIsNone(solver._force_color((0, 1), 1))
        self.assertEqual((solver.state, solver.count), (state_before, count_before))

    def test_force_in_line(self):
        """Test Solve._force_in_line in level1 file"""
        solver = self.solver1
        self.assertEqual(set(solver._force_in_line(2)), {((0, 1), 2)})
        self.assertEqual(set(solver._force_in_line(5)), {((1, -2), 1)})
        self.assertEqual(set(solver._force_in_line(1)), {((-1, -1), 2)})

    def test_propagate(self):
        """Test Solve._propagate in different situations"""

        # a single gold cell forces nothing -> [] (not None)
        solver = self.solver_empty_radius1
        solver._place((0, 0), 1)
        self.assertEqual(solver._propagate([(0, 0)]), [])

        # a wrong extra cell causes a contradiction -> None, all forced cells undone
        solver = self.solver1
        solver._place((1, -2), 2)        # the solution has gold here
        state_before = dict(solver.state)
        count_before = [row[:] for row in solver.count]
        seeds = [c for c, color in solver.state.items() if color != 0]
        self.assertEqual((solver._propagate(seeds), solver.state, solver.count),(None, state_before, count_before))

    def test_search_with_propagation(self):
        """Test basice search + propagation"""
        def search(path):
            solver = Solve(Board(path), use_propagation=True)
            solver.search()
            return solver.solutions

        # 1. unique solution is found and is the right one
        self.assertEqual(search("test_data/level1.txt"),
                         [Board("test_data/solution1.txt").axial])
        # 2. many solutions: exactly two are collected
        self.assertEqual(len(search("test_data/level1-many.txt")), 2)
        # 3. no solution
        self.assertEqual(search("test_data/level1-nosolution.txt"), [])

    def test_pick_cell(self):
        """Test the fail-first cell selection (_pick_cell)."""
        solver = self.solver1
        state_before = dict(solver.state)
        count_before = [row[:] for row in solver.count]
        coord, legal = solver._pick_cell()
        evaluated = solver.failfirst_checks

        self.assertEqual((solver.state, solver.count), (state_before, count_before))

        # picks an empty cell with the fewest legal colours (MRV), and
        # evaluates every empty cell once (no empty domain to stop early)
        self.assertEqual((solver.state[coord], evaluated), (0, len(solver.empty)))
        self.assertEqual(len(legal), min(len(solver._legal_colors(c)) for c in solver.empty)) # type: ignore

        #the one on the most-filled lines is chosen
        improved = Solve(self.level1, use_failfirst=True, improved_ff=True)
        def filled(c):
            return sum(sum(improved.count[lid]) for _, lid in improved.cell_lines[c])
        sizes = {c: len(improved._legal_colors(c)) for c in improved.empty}
        smallest = min(sizes.values())
        best_filled = max(filled(c) for c in sizes if sizes[c] == smallest)
        coord, legal = improved._pick_cell()
        self.assertEqual((len(legal), filled(coord)), (smallest, best_filled)) # type: ignore

    def test_solver_passes_checker(self):
        """Feed solver output into Check (independent cross-validation)."""
        # basic DFS on a unique level: the solution passes the checker
        self.solver1.search()
        found = state_to_board(2, self.solver1.solutions[0])
        self.assertTrue(Check(self.level1).check_solution(found))

        # both solutions found for a "many" level pass the checker
        self.solver1_many.search()
        checker_many = Check(self.level1_many)
        self.assertTrue(all(
            checker_many.check_solution(state_to_board(self.level1_many.radius, s))
            for s in self.solver1_many.solutions
        ))

        # propagation + fail-first gives a board that passes and is identical
        fast = Solve(self.level1, use_propagation=True, use_failfirst=True)
        fast.search()
        self.assertEqual(fast.solutions, self.solver1.solutions)
        self.assertTrue(Check(self.level1).check_solution(
            state_to_board(2, fast.solutions[0])))

    def test_print_result(self):
        """Test the print format"""
        solver = self.solver1
        solver.search()
        self.assertEqual(solver.print_result(), SOLUTION1_PRINT)


        
if __name__ == "__main__":
    unittest.main()
