from PyQt5.QtCore import QObject


class Cell(QObject):
    """
    This class represents a cell in Conway's Game of Life.

    Args:
        x (int): The x-coordinate of the cell.
        y (int): The y-coordinate of the cell.
        init_state (int): The initial state of the cell (0 for dead, 1 for alive).
        init_age (int): The initial age of the cell.

    Attributes:
        _x (int): The x-coordinate of the cell.
        _y (int): The y-coordinate of the cell.
        _state (int): The current state of the cell (0 for dead, 1 for alive).
        _age (int): The current age of the cell.

    """

    def __init__(self, x, y, init_state, init_age):
        """
        Initializes a new instance of Cell.
        """
        super().__init__()
        self._x = x
        self._y = y
        self._state = init_state
        self._age = init_age

    @property
    def state(self):
        """Returns the current state of the cell (0 for dead, 1 for alive)."""
        return self._state

    @state.setter
    def state(self, new_state):
        """Sets the state of the cell."""
        self._state = new_state

    @property
    def age(self):
        """Returns the current age of the cell."""
        return self._age

    @age.setter
    def age(self, new_age):
        """Sets the age of the cell."""
        self._age = new_age

    def toggle(self):
        """Toggles the state of the cell (dead to alive, alive to dead)."""
        self._state = 1 - self._state

    def __str__(self):
        """
        Returns a string representation of the cell.

        The string includes the coordinates, state, and age of the cell.
        """
        return f"({self._x}, {self._y}) - {'Alive' if self._state == 1 else 'Dead' } - Age: {self._age}"


