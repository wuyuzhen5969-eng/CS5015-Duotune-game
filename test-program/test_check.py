
"""Unit tests for the Duotone board and checker."""

import unittest

from check import Board, Check


class TestBoard(unittest.TestCase):
    """Test the Board class."""

    def test_read_board(self):
        """Test reading boards with different files."""
        board1 = Board("test_data/level1.txt")
        board3 = Board("test_data/level3.txt")

        self.assertEqual(board1.radius, 2)
        self.assertEqual(len(board1.board), 5)
        self.assertEqual(
            [len(row) for row in board1.board],
            [3, 4, 5, 4, 3]
        )

        self.assertEqual(board3.radius, 3)
        self.assertEqual(len(board3.board), 7)
        self.assertEqual(
            [len(row) for row in board3.board],
            [4, 5, 6, 7, 6, 5, 4]
        )

    def test_convert_to_axial(self):
        """Test conversion from nested lists to axial coordinates."""
        board = Board("test_data/solution1.txt")

        expected = {
            (-2, 0): 1,
            (-2, 1): 2,
            (-2, 2): 2,
            (-1, -1): 2,
            (-1, 0): 2,
            (-1, 1): 1,
            (-1, 2): 1,
            (0, -2): 2,
            (0, -1): 1,
            (0, 0): 1,
            (0, 1): 2,
            (0, 2): 2,
            (1, -2): 1,
            (1, -1): 2,
            (1, 0): 2,
            (1, 1): 1,
            (2, -2): 2,
            (2, -1): 1,
            (2, 0): 1
        }

        self.assertEqual(board.axial, expected)

    def test_get_lines(self):
        """Test extraction of lines in all three directions."""
        board = Board("test_data/solution1.txt")

        self.assertEqual(len(board.lines), 3)

        for direction_index, direction in enumerate(board.lines):
            self.assertEqual(len(direction), 5)

            # Check the number of cells in each line.
            self.assertEqual(
                [len(line) for line in direction],
                [3, 4, 5, 4, 3]
            )

            # Check that all cells appear exactly once.
            coordinates = [
                cell[0]
                for line in direction
                for cell in line
            ]

            self.assertEqual(len(coordinates), 19)
            self.assertEqual(set(coordinates), set(board.axial))

            # Check grouping and ordering.
            for line in direction:
                if direction_index == 0:
                    # Fixed q, sorted by r.
                    self.assertEqual(
                        len({cell[0][0] for cell in line}), 1
                    )
                    values = [cell[0][1] for cell in line]
                    

                elif direction_index == 1:
                    # Fixed r, sorted by q.
                    self.assertEqual(
                        len({cell[0][1] for cell in line}), 1
                    )
                    values = [cell[0][0] for cell in line]

                else:
                    # Fixed -q-r, sorted by q.
                    self.assertEqual(
                        len({
                            -cell[0][0] - cell[0][1]
                            for cell in line
                        }),
                        1
                    )
                    values = [cell[0][0] for cell in line]

                self.assertEqual(values, sorted(values))


class TestCheck(unittest.TestCase):
    """Test the Check class."""

    def setUp(self):
        self.level1 = Board("test_data/level1.txt")
        self.checker1 = Check(self.level1)

        self.solution1 = Board("test_data/solution1.txt")
        self.flipped = Board("test_data/solution1-flipped.txt")

        self.level2 = Board("test_data/level2.txt")
        self.level3 = Board("test_data/level3.txt")

    def make_line(self, colors):
        """Create a line for isolated rule testing."""
        return [
            ((index, 0), color)
            for index, color in enumerate(colors)
        ]

    def test_check_radius(self):
        """Test whether the candidate has the same radius as the level."""
        self.assertTrue(
            self.checker1._check_radius(self.solution1)
        )
        self.assertFalse(
            self.checker1._check_radius(self.level3)
        )

    def test_check_colors(self):
        """Test colour completion and preservation of given colours."""
        self.assertTrue(
            self.checker1._check_colors(self.solution1)
        )

        # The flipped solution changes no originally given cells.
        self.assertTrue(
            self.checker1._check_colors(self.flipped)
        )

        # Level 2 is incomplete and therefore cannot be a solution.
        checker2 = Check(self.level2)
        self.assertFalse(
            checker2._check_colors(self.level2)
        )

        # Solution 1 does not preserve all given colours in level 2.
        self.assertFalse(
            checker2._check_colors(self.solution1)
        )

    def test_check_no_three(self):
        """Test the no-three-consecutive-cells rule."""
        self.assertTrue(
            self.checker1._check_no_three(self.solution1)
        )
        self.assertFalse(
            self.checker1._check_no_three(self.flipped)
        )

        # Isolate the rule with a line that has valid colour balance.
        candidate = self.solution1
        candidate.lines = (
            [self.make_line([1, 1, 1, 2, 2])],
            [],
            []
        )

        self.assertFalse(
            self.checker1._check_no_three(candidate)
        )

    def test_check_balance(self):
        """Test the colour balance rule."""
        self.assertTrue(
            self.checker1._check_balance(self.solution1)
        )
        self.assertFalse(
            self.checker1._check_balance(self.flipped)
        )

        # Isolate the rule: no three consecutive cells are identical,but the difference between colour counts is 2.
        candidate = Board("test_data/solution1.txt")
        candidate.lines = (
            [self.make_line([1, 2, 1, 1])],
            [],
            []
        )

        self.assertFalse(
            self.checker1._check_balance(candidate)
        )

    def test_check_solution(self):
        """Test the complete solution checker."""
        self.assertTrue(
            self.checker1.check_solution(self.solution1)
        )

        self.assertFalse(
            self.checker1.check_solution(self.flipped)
        )

        self.assertFalse(
            self.checker1.check_solution(self.level3)
        )

        checker2 = Check(self.level2)
        self.assertFalse(
            checker2.check_solution(self.solution1)
        )


if __name__ == "__main__":
    unittest.main()
