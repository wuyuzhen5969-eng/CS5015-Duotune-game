"""Seek for solutions(partially, state colored-changing chessboard) for Duotone using DFS."""

import sys

from check import Board


class Solve: 
    "Seek for solutions to Duotone."
    def __init__(self, level: Board, use_propagation = False, use_failfirst = False, improved_ff = False):
        """initialize the solver"""
        self.state = dict(level.axial)
        self.radius = level.radius
        self.color = [1, 2]

        self.use_propagation = use_propagation
        self.use_failfirst = use_failfirst
        self.improved_ff = improved_ff

        self.nodes = 0
        self.backtracks = 0
        self.forced_count = 0
        self.failfirst_checks = 0
        self.solutions = []

        # Identify empty cells.
        self.empty = [coord for coord, color in self.state.items() if color == 0]

        #line(id) → cells
        self.line_list = self._build_line(level)

        #cell → 3 lines.
        self.cell_lines = self._build_cell_lines()

        # initialize the origin color count and bound for each line
        self.count, self.bound = self._initialise_counts()

    def _build_line(self, level: Board) -> list[list[tuple[int, int]]]:
        """Build a axial list of line and assign line IDs with its index"""
        # the color value keep state-changing during seeking, so distract axis from color.
        lines = [[[coord for coord, _ in line] for line in direction] for direction in level.lines]
        line_list = []
        for direction in lines:
            for line in direction:
                line_list.append(line)
        return line_list

    def _build_cell_lines(self) ->dict[tuple[int, int], list[tuple[int, int]]]:
        """Map each cell to its positions in the corresponding lines."""
        cell_lines = {coord: [] for coord in self.state}
        for lid, line in enumerate(self.line_list):
            for index, coord in enumerate(line):
                cell_lines[coord].append((index, lid))
        return cell_lines

    def _initialise_counts(self) -> tuple[list[list[int]], list[int]]:
        """Initialise color counts and maximum allowed counts bound for each line"""
        count = []
        bound = []
        for lid, line in enumerate(self.line_list):
            bound.append((len(line) + 1) // 2)
            count.append([0, 0])
            for coord in line:
                color = self.state[coord]
                if color != 0:
                    count[lid][color - 1] += 1
        return count, bound

    def _check_no_three(self, coord: tuple[int, int]) -> bool:
        """Check whther placing a color creates three consecutive cells with the same color"""
        for index, lid in self.cell_lines[coord]:
            line = self.line_list[lid]
            for s in (index - 2, index - 1, index):
                if 0 <= s < len(line) - 2:
                    cell1, cell2, cell3 = (self.state[pair] for pair in line[s: s+3])
                    if cell1 == cell2 == cell3 != 0:
                        return False
        return True

    def _check_balance(self, coord: tuple[int, int]) -> bool:
        """Check whether either color exceeds the line's upper bound."""
        for _, lid in self.cell_lines[coord]:
            gold, blue = self.count[lid]
            if gold > self.bound[lid] or blue > self.bound[lid]:
                return False
        return True

    def _place(self, coord: tuple[int, int], color: int):
        """place a color and update the affected line counts"""
        self.state[coord] = color
        for _, lid in self.cell_lines[coord]:
            self.count[lid][color - 1] += 1

    def _remove(self, coord: tuple[int, int]):
        """Remove a color and restore the affected line counts."""
        color = self.state[coord]
        self.state[coord] = 0
        for _, lid in self.cell_lines[coord]:
            self.count[lid][color - 1] -= 1

    def search(self):
        """Depth first search with optional constraint propagation and fail first"""
        # stop searching after finding two solutions
        if len(self.solutions) >= 2:
            return

        if self.use_failfirst:
            coord, domain = self._pick_cell()

        else:
            #Find the first cell that is stil empty
            coord = next((coord for coord in self.empty if self.state[coord] == 0), None)
            domain = self.color
        #Base case: all empty cells has been assigned

        if coord is None:
            self.solutions.append(dict(self.state))
            return

        if not domain:
            self.backtracks += 1
            return

        for color in domain: # type: ignore
            self._place(coord, color) #decision assignment
            self.nodes += 1

            if self._check_no_three(coord) and self._check_balance(coord):

                 #constraint propagation block
                if self.use_propagation:
                    forced = self._propagate([coord]) #forced assignment
                    if forced is not None:
                        self.search()
                        for cell in reversed(forced):
                            self._remove(cell)
                    else:
                        self.backtracks += 1

                else:
                    self.search()

            else:
                self.backtracks += 1
            
            self._remove(coord)

            # Propagate the stopping condition to upper recursion levels.
            if len(self.solutions) >= 2:
                return

    
    """Imporvement: constraint propagation"""
    def _force_color(self, coord: tuple[int, int], color: int) -> str | None:
        """Force a cell to take a specific color."""
        current = self.state[coord]

        #The cell has already been assigned
        if current != 0:
            return "same" if current == color else None

        self._place(coord, color)
        if self._check_no_three(coord) and self._check_balance(coord):
            return "placed"
        self._remove(coord)
        return None

    def _force_in_line(self, lid: int) -> list[tuple]:
        """Scan a line, and return a list of cells to be forced """
        line = self.line_list[lid]
        n = len(line)
        tobe_forced = []

        #rule 1: aa -> both sides differ
        for i in range(n - 1):
            a = self.state[line[i]]
            if a != 0 and a == self.state[line[i + 1]]:
                for j in (i - 1, i + 2):
                    if 0 <= j < n and self.state[line[j]] == 0:
                        tobe_forced.append((line[j], 3 - a))

        #rule 2: a_a -> middle differ
        for i in range(n - 2):
            a = self.state[line[i]]
            if a!= 0 and a == self.state[line[i + 2]] and self.state[line[i + 1]] == 0:
                tobe_forced.append((line[i + 1], 3 - a))

        #rule 3: color at its bound
        for color in self.color:
            if self.count[lid][color - 1] == self.bound[lid]:
                for coord in line:
                    if self.state[coord] == 0:
                        tobe_forced.append((coord, 3 - color))
        return tobe_forced

    def _propagate(self, seeds: list[tuple]) -> list[tuple] | None:
        """Return the list of cells forced, or None on contradiction."""
        forced = []
        worklist = list(seeds)
        cursor = 0
        while cursor < len(worklist):
            coord = worklist[cursor]
            cursor += 1
            for _, lid in self.cell_lines[coord]:
                for target, color in self._force_in_line(lid):
                    result = self._force_color(target, color)
                    if result is None:
                        for cell in reversed(forced):
                            self._remove(cell)
                        return None
                    if result == "placed":
                        forced.append(target)
                        worklist.append(target)
                        self.forced_count += 1
        return forced


    """Imporvement: Fail first(MRV)"""
    def _legal_colors(self, coord: tuple) -> list:
        self.failfirst_checks += 1
        legal = []
        for color in self.color:
            self._place(coord, color)
            if self._check_no_three(coord) and self._check_balance(coord):
                legal.append(color)
            self._remove(coord)
        return legal

    def _pick_cell(self):
        best, best_legal, best_key = None, None, None
        for coord in self.empty:
            if self.state[coord] != 0:
                continue
            legal = self._legal_colors(coord)
            key = len(legal)

            #choose the cell with the fewest legal colors  on the line that is already the most filled.
            if self.improved_ff:
                filled = sum(sum(self.count[lid]) for _, lid in self.cell_lines[coord])
                key = (len(legal), -filled)
            
            if best is None or key < best_key: # type: ignore
                best, best_legal, best_key = coord, legal, key 
                if key == 0:
                    break               
        return best, best_legal

    def print_result(self):
        result = len(self.solutions)
        if result == 0:
            return f"no"
        
        if result == 1:
            length = 2 * self.radius + 1
            result_state = [[] for _ in range(length)]
            for ((q, _), color) in self.solutions[0].items():
                result_state[q + self.radius].append(color)
            parts = [str(self.radius)]
            for line in result_state:
                parts.append(' ' * (length -len(line)) + ' '.join(map(str, line)))
            output = '\n'.join(parts)
            return output
            
        if result == 2:
            return f"many"



def main():
    level = Board(sys.argv[1])
    solver = Solve(level, True, True)
    seeds = [coord for coord, color in solver.state.items() if color != 0]
    if solver._propagate(seeds) is not None:
        solver.search()
    print(solver.print_result())
    

if __name__ == "__main__":
    main()
