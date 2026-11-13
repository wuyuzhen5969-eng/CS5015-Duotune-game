
"""Checker for a proposed solution(completed, color-snapped chessboard) for Duotone."""

import sys


class Board:
    """Represent a hexagonal board and gets lines in three direction."""

    def __init__(self, file_path: str):
        """Initialise the board and its representations."""
        self.radius, self.board = self._read_board(file_path)
        self.axial = self.convert_to_axial()
        self.lines = self.get_lines()

    @staticmethod
    def _read_board(file_path: str) -> tuple[int, list[list[int]]]:
        """Read the radius and board data from a file."""
        with open(file_path, encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
            radius = int(lines[0])
            board = [
                [int(color) for color in line.split()]
                for line in lines[1:]
            ]

        return radius, board

    def convert_to_axial(self) -> dict:
        """Convert the board into axial coordinates.

        Axial coordinates are represented as (q, r):
        - q follows the row direction.
        - r follows the down-right direction.
        - -q-r follows the up-right direction.
        """
        axial = {}

        for i, row in enumerate(self.board):
            for j, color in enumerate(row):
                q = i - self.radius
                r = max(-i, -self.radius) + j
                axial[(q, r)] = color

        return axial

    def get_lines(self) -> tuple[list, list, list]:
        """Extract lines in the three directions."""
        row, down_right, up_right = (
            [[] for _ in range(2 * self.radius + 1)]
            for _ in range(3)
        )

        for (q, r), color in self.axial.items():
            row[q + self.radius].append(((q, r), color))
            down_right[r + self.radius].append(((q, r), color))
            up_right[-r - q + self.radius].append(((q, r), color))

        for line in row:
            line.sort(key=lambda cell: cell[0][1])

        for line in down_right:
            line.sort(key=lambda cell: cell[0][0])

        for line in up_right:
            line.sort(key=lambda cell: cell[0][0])

        return row, down_right, up_right
    

class Check():
    """Check whether a solution board satisfies the requirements."""
    def __init__(self, level: Board):
        self.level = level

    def _check_radius(self, solution: Board) -> bool:
        """Check whether two boards have the same radius."""
        return self.level.radius == solution.radius

    def _check_colors(self, solution: Board) -> bool:
        """Check solution colours and preserve the given colours."""
        if not set(solution.axial.values()) <= {1, 2}:
            return False

        for coord, color in self.level.axial.items():
            if color != 0 and color != solution.axial[coord]:
                return False

        return True

    def _check_no_three(self, solution: Board) -> bool:
        """Check that no three consecutive cells share the same colour."""
        for direction in solution.lines:
            for line in direction:
                for i in range(len(line) - 2):
                    if (
                        line[i][1]
                        == line[i + 1][1]
                        == line[i + 2][1]
                    ):
                        return False

        return True

    def _check_balance(self, solution: Board) -> bool:
        """Check that colour counts differ by at most one in each line."""
        for direction in solution.lines:
            for line in direction:
                gold_total = 0
                blue_total = 0

                for pair in line:
                    if pair[1] == 1:
                        gold_total += 1
                    else:
                        blue_total += 1

                if abs(gold_total - blue_total) > 1:
                    return False

        return True

    def check_solution(self, solution: Board) -> bool:
        """Check whether the proposed solution satisfies all requirements."""
        if not self._check_radius(solution):
            return False

        if not self._check_colors(solution):
            return False

        if not self._check_no_three(solution):
            return False

        if not self._check_balance(solution):
            return False

        return True


def main():
    """Run the solution checker."""
    level = Board(sys.argv[1])
    check_level = Check(level)
    solution = Board(sys.argv[2])

    print("yes" if check_level.check_solution(solution) else "no")


if __name__ == "__main__":
    main()
