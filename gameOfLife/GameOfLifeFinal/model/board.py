import numpy as np

from GameOfLifeFinal.model.observer import Observable


class Board(Observable):
    """
    This class represents the Game of Life board.

    Args:
        init_board (numpy.ndarray): An initial NumPy matrix representing the initial state of the board.

    Attributes:
        _board (numpy.ndarray): The matrix representing the current state of the board.

    Signals(observer.py):
        valueChanged: Signal emitted when the state of the board changes.

    """

    def __init__(self, init_board):
        """
        Initializes a new instance of Board.
        """
        super().__init__(init_board)
        self._board = init_board

    @property
    def width(self):
        """Returns the width of the board."""
        return self._board.shape[1]

    @property
    def height(self):
        """Returns the height of the board."""
        return self._board.shape[0]

    def get_cell(self, x, y):
        """
        Gets the state of a specific cell on the board.

        Args:
            x (int): The x-coordinate of the cell.
            y (int): The y-coordinate of the cell.

        Returns:
            int: The state of the cell (0 for dead, 1 for alive).
        """
        return self._board[y, x]

    def toggle_cell(self, x, y):
        """
        Toggles the state of a specific cell, sets the age to 1 and signals the update.

        Args:
            x (int): The x-coordinate of the cell.
            y (int): The y-coordinate of the cell.
        """
        self._board[y, x].toggle()
        self._board[y, x].age = 1
        self.value = self._board

    def set_board(self, new_board):
        """
        Sets a new board with a specific state and signals the update.

        Args:
            new_board (numpy.ndarray): The new board to set.
        """
        self._board = new_board
        self.value = new_board

    def update(self):
        """
        Updates the state of the board following the rules of the Game of Life.

        This method iterates through each cell on the board, applies the rules of the
        Game of Life, and updates the state accordingly. It also takes care of updating
        the age of cells and signals the update.
        """
        # new auxiliary board on which safely perform updates
        new_board_states = np.array([[cell.state for cell in row] for row in self._board])
        for y in range(self._board.shape[0]):
            for x in range(self._board.shape[1]):
                cell = self._board[y, x]
                live_neighbors = self.count_live_neighbors(x, y, self._board)

                # Apply the rules of Conway's Game of Life
                if cell.state == 1 and (live_neighbors < 2 or live_neighbors > 3):
                    new_board_states[y][x] = 0
                elif cell.state == 0 and live_neighbors == 3:
                    new_board_states[y][x] = 1

        # Update board states and cells age
        for y in range(self._board.shape[0]):
            for x in range(self._board.shape[1]):
                self._board[y, x].state = new_board_states[y, x]
                # If the state is 1 increment cell age
                if self._board[y, x].state:
                    self._board[y, x].age += 1
                else:
                    self._board[y, x].age = 0

        self.value = self._board

    def count_live_neighbors(self, x, y, board):
        """
        Counts the number of live neighbors for a cell.

        Args:
            x (int): The x-coordinate of the cell.
            y (int): The y-coordinate of the cell.
            board (numpy.ndarray): The board on which to perform the count.

        Returns:
            int: The number of live neighbors.

        This method counts the number of live neighbors around a specific cell
        on the board. It considers the eight adjacent cells and increments the count
        for each live neighbor.
        """
        live_neighbors = 0

        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip the current cell
                new_x, new_y = x + dx, y + dy

                # Check for boundaries
                if 0 <= new_x < self._board.shape[1] and 0 <= new_y < self._board.shape[0]:
                    if board[new_y][new_x].state == 1:
                        live_neighbors += 1

        return live_neighbors
