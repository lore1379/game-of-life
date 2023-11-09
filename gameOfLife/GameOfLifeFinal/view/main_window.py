import json
import os
import sys
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsRectItem, QDialog, QMessageBox
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from GameOfLifeFinal.model.board import Board
from GameOfLifeFinal.model.cell import Cell
from Ui_GameOfLife import Ui_MainWindow
from Ui_AboutDialog import Ui_Dialog
from Ui_LoadPatternDialog import Ui_LoadPatternDialog


class MainWindow(QMainWindow):
    """
    This class represents the main window (Controller) of the Game of Life application.

    Args:
        game_board (Board): The game board model.

    Attributes:
        explained in detail in the init method
    """

    def __init__(self, game_board):
        """Initializes a new instance of MainWindow."""
        super().__init__()

        # Reference to the game board model.
        self._game_board = game_board
        # Reference to the current state of the game board.
        self._game_board_grid = game_board.value

        # Load the UI from the .ui file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create about dialog and load pattern dialog and wire actions
        self._aboutDialog = AboutDialog()
        self._loadPatternDialog = LoadPatternDialog()
        self.ui.actionAbout.triggered.connect(self._aboutDialog.exec_)
        self.ui.actionQuit.triggered.connect(QApplication.exit)
        self.ui.patternButton.clicked.connect(self._loadPatternDialog.exec_)

        # Set up the scene for the game board
        self.scene = QGraphicsScene(self)
        self.ui.boardView.setScene(self.scene)

        """Initialize UI elements and set initial values."""
        # initialize starting cell size
        self._cell_size = 15
        # Find start/pause button widget in ui
        self._startPauseButton = self.ui.startPauseButton
        # Find frame rate slide and label widgets in ui
        self._frameRateSlider = self.ui.frameRateSlider
        self._frameRateLabel = self.ui.frameRateLabel
        # set initial text of the frame rate label
        self._frameRateLabel.setText(f"Frame Rate: {self._frameRateSlider.value()}")

        """Connect signals to their respective slots."""
        self.ui.startPauseButton.clicked.connect(lambda: self.start_pause_simulation())
        self.ui.nextGenButton.clicked.connect(lambda: self.next_generation())
        self.ui.clearButton.clicked.connect(lambda: self.clear_board())
        # Connect mouse events to handle panning
        self.ui.boardView.mousePressEvent = self.mouse_press_event
        self.ui.boardView.mouseMoveEvent = self.mouse_move_event
        self.ui.boardView.mouseReleaseEvent = self.mouse_release_event
        # Connect the slider valueChanged signal to the updateFrameRateLabel method
        self._frameRateSlider.valueChanged.connect(self.update_frame_rate_label)
        # Signal to update_frame_rate method
        self.ui.frameRateSlider.valueChanged.connect(lambda: self.update_frame_rate(self._frameRateSlider.value()))
        # Signal to update_cell_size method
        self.ui.zoomSlider.valueChanged.connect(lambda: self.update_cell_size(self.ui.zoomSlider.value()))
        # Signal to resize_grid method
        self.ui.resizeButton.clicked.connect(lambda: self.resize_grid(self.ui.sizeBox.value()))
        # Signal from load pattern dialog to call the load pattern method
        self._loadPatternDialog.patternSelected.connect(self.load_pattern)

        """ Observe board for changes """
        game_board.register(self.update_view)

        """ Logic Variables """
        # Flag indicating whether the simulation is paused.
        self._paused = True
        # Flag indicating whether a drag operation is in progress.
        self._drag_in_progress = False
        # Last recorded mouse position.
        self._last_mouse_pos = None
        # Timer for simulation updates.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        # Current generation count.
        self._current_generation = 0
        # Count of alive cells in the current generation.
        self._alive_cells = 0

        """ First load of ui with initialized board """
        self.update_view(game_board.value)

    def clear_board(self):
        """
        Clears the game board if game paused, resets the generation count, clears the log, and updates the view.

        This method is called when the user initiates a clear operation. It resets the current generation count,
        clears the log browser, creates a new empty board, and sets the new board to the game board model.

        """
        if self._paused:
            # Reset generation count
            self._current_generation = 0
            # Clear the log browser
            self.ui.logBrowser.clear()
            # Create a new empty board
            new_board = np.array([[Cell(x, y, 0, 0) for x in range(self._game_board_grid.shape[1])]
                                  for y in range(self._game_board_grid.shape[0])], dtype=object)
            # Set the new board to the game board model
            self._game_board.set_board(new_board)

    def update_view(self, game_board_grid):
        """
        Updates the graphical representation of the game board in the UI.

        This method is called when the game board model changes. It updates the internal reference to the game board,
        initializes the count of alive cells, clears the graphical scene, and draws the new state of the game board.

        Args:
            game_board_grid (numpy.ndarray): The current state of the game board.

        """
        # update the reference to the model
        self._game_board_grid = game_board_grid
        # initialize alive_cells count
        self._alive_cells = 0
        # clear the scene
        self.scene.clear()
        # Draw the board
        for y in range(game_board_grid.shape[0]):
            for x in range(game_board_grid.shape[1]):
                cell = QGraphicsRectItem(x * self._cell_size, y * self._cell_size, self._cell_size, self._cell_size)
                # Get the age of the cell (age color will vary in the range [0, 10])
                age = min(game_board_grid[y, x].age, 10)
                # Adjusted starting hue
                hue = (0.5 + age / 20.0) % 1.0
                # Calculate color based on age (light blue to bright red gradient)
                color = QColor.fromHslF(hue, 1.0, 0.5)
                if game_board_grid[y, x].state:
                    cell.setBrush(QBrush(color))
                    self._alive_cells += 1
                else:
                    QBrush(Qt.white)
                self.scene.addItem(cell)

    def update_log(self, message):
        """
        Appends a message to the log browser in the UI.

        This method is called to update the log browser in the UI with a new message.

        Args:
            message (str): The message to append to the log.

        """
        self.ui.logBrowser.append(message)

    def mouse_press_event(self, event):
        """
        Handles the mouse press event.

        Registers the mouse position when the user presses the mouse button.

        Args:
            event (QMouseEvent): The mouse press event.

        """
        self._last_mouse_pos = event.pos()

    def mouse_move_event(self, event):
        """
        Handles the mouse move event.

        Calculates the difference in mouse position from the initial press, checks if it exceeds a threshold, and
        switches to drag mode if necessary. Handles panning if in drag mode.

        Args:
            event (QMouseEvent): The mouse move event.

        """
        # Calculate the difference in mouse position from the initial press
        delta = event.pos() - self._last_mouse_pos

        # Check if the delta is greater than a threshold
        threshold = 10  # 10 pixels
        if delta.manhattanLength() > threshold:
            # change to drag mode
            self._drag_in_progress = True
            # Change cursor to indicate panning
            self.setCursor(Qt.ClosedHandCursor)

        if self._drag_in_progress:
            # Handle panning
            delta = event.pos() - self._last_mouse_pos
            self.ui.boardView.verticalScrollBar().setValue(self.ui.boardView.verticalScrollBar().value() - delta.y())
            self.ui.boardView.horizontalScrollBar().setValue(
                self.ui.boardView.horizontalScrollBar().value() - delta.x())
            self._last_mouse_pos = event.pos()

    def mouse_release_event(self, event):
        """
        Handles the mouse release event.

        Resets drag mode if in progress or performs a click action based on the mouse position in the view.

        Args:
            event (QMouseEvent): The mouse release event.

        """
        # Reset drag mode
        if self._drag_in_progress:
            self._drag_in_progress = False
            self.setCursor(Qt.ArrowCursor)  # Change cursor back to the arrow
        # Perform click action
        else:
            # Position in the view
            view_pos = self.ui.boardView.mapToScene(event.pos())
            # Find x, y position of the cell in the grid
            cell_x = int(view_pos.x() // self._cell_size)
            cell_y = int(view_pos.y() // self._cell_size)
            # Check if coordinates are in the board
            if 0 <= cell_x < self._game_board_grid.shape[1] and 0 <= cell_y < self._game_board_grid.shape[0]:
                self.cell_clicked(cell_x, cell_y)

    def cell_clicked(self, x, y):
        """
        Handles the click on a cell in the game board.

        This method is called when a user clicks on a cell in the game board view. It toggles the value of the cell
        (alive or dead) if the game is paused.

        Args:
            x (int): The x-coordinate of the clicked cell.
            y (int): The y-coordinate of the clicked cell.

        """
        # Permitted when game paused
        if self._paused:
            # Toggle cell value
            self._game_board.toggle_cell(x, y)

    def start_pause_simulation(self):
        """
        Start or pause the simulation based on the current state.

        If the simulation is paused, this method starts it, updates button states,
        and changes the button text to "Pause".
        If the simulation is running, it pauses it, updates button states,
        and changes the button text to "Start".
        """
        if self._paused:
            # Starting simulation
            self._paused = False
            # Disable buttons that works if paused
            self.ui.clearButton.setEnabled(False)
            self.ui.nextGenButton.setEnabled(False)
            self.ui.resizeButton.setEnabled(False)
            self.ui.patternButton.setEnabled(False)
            self.timer.start(1000 // self._frameRateSlider.value())  # Set your desired interval in milliseconds
            self._startPauseButton.setText("Pause")
        else:
            # Stopping simulation
            self._paused = True
            # Enable buttons that works if paused
            self.ui.clearButton.setEnabled(True)
            self.ui.nextGenButton.setEnabled(True)
            self.ui.resizeButton.setEnabled(True)
            self.ui.patternButton.setEnabled(True)
            self.timer.stop()
            self._startPauseButton.setText("Start")

    def next_generation(self):
        """
        Progresses the simulation by one generation.

        This method is called when the user manually triggers the progression to the next generation. It updates
        the game board, increments the generation count, and logs the information.
        """
        # Single generation progression permitted only when game is paused
        if self._paused:
            self._game_board.update()
            self._current_generation += 1
            self.update_log(f"Generation {self._current_generation} - Alive Cells: {self._alive_cells}\n")

    def update_simulation(self):
        """
        Update the simulation based on the timer interval.

        This method is connected to the timer and is called at each interval when the simulation is running.
        It updates the game board, increments the generation count, and logs the information.
        """
        # Permitted when game is not paused
        if not self._paused:
            self._game_board.update()
            self._current_generation += 1
            self.update_log(f"Generation {self._current_generation} - Alive Cells: {self._alive_cells}\n")

    def update_frame_rate_label(self, value):
        """
        Update the frame rate label based on the slider value.

        Args:
            value (int): The selected frame rate value from the slider.

        This method is connected to the frame rate slider's valueChanged signal
        and updates the frame rate label accordingly.
        """
        self._frameRateLabel.setText(f"Frame Rate: {value}")

    def update_frame_rate(self, value):
        """
        Update the frame rate based on the slider value.

        Args:
            value (int): The selected frame rate value from the slider.

        This method is connected to the frame rate slider's valueChanged signal
        and updates the frame rate value if the timer is active.
        """
        if self.timer.isActive():
            self.timer.start(1000 // value)

    def update_cell_size(self, value):
        """
        Update the cell size and refresh the board representation.

        Args:
            value (int): The selected cell size value from the zoom slider.

        This method is connected to the zoom slider's valueChanged signal and updates the cell size,
        refreshing the board representation.
        """
        self._cell_size = value
        self.update_view(self._game_board_grid)

    def resize_grid(self, value):
        """
        Resize the game board grid when the game is paused.

        Args:
            value (int): The selected size value from the size box.

        This method is connected to the resize button's clicked signal
        and creates a new blank board with the new size if the game is paused.
        """
        if self._paused:
            # Creating a new blank board with the new size
            new_board = np.array([[Cell(x, y, 0, 0) for x in range(value)]
                                  for y in range(value)], dtype=object)
            self._game_board.set_board(new_board)

    def load_pattern(self, pattern):
        """
        Load a pattern onto the game board when the game is paused.

        Args:
            pattern (list): A list of (x, y) coordinates representing the pattern.

        This method is connected to the patternSelected signal from the load pattern dialog
        and loads the selected pattern onto the game board if the game is paused.
        """
        if self._paused:
            # Create e new board
            new_board = np.array([[Cell(x, y, 0, 0) for x in range(self._game_board_grid.shape[1])]
                                  for y in range(self._game_board_grid.shape[0])], dtype=object)
            # Get starting coordinates
            start_x = self.ui.startXSpinBox.value()
            start_y = self.ui.startYSpinBox.value()
            for cell_y, cell_x in pattern:
                target_x = cell_x + start_x
                target_y = cell_y + start_y
                # Set states starting from provided coordinates
                if 0 <= target_x < self._game_board_grid.shape[1] and 0 <= target_y < self._game_board_grid.shape[0]:
                    new_board[target_y, target_x].state = 1

            self._game_board.set_board(new_board)
        # Close the dialog
        self._loadPatternDialog.accept()


class AboutDialog(QDialog):
    """Initialize the AboutDialog."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set up the user interface from Designer
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)


class LoadPatternDialog(QDialog):
    # Custom signal to emit the selected pattern
    patternSelected = pyqtSignal(list)

    def __init__(self, **kwargs):
        """Initialize the LoadPatternDialog."""
        super().__init__(**kwargs)

        # Set up the user interface from Designer
        self.ui = Ui_LoadPatternDialog()
        self.ui.setupUi(self)

        # Get GameOfLifeFinal folder
        parent_folder = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

        # Open the folder and find patterns
        with open(os.path.join(parent_folder, "cells/patterns.json"), "r") as f:
            self.patterns = json.load(f)

        # Add patterns to list widget
        for pattern_name in self.patterns:
            self.ui.patternsListWidget.addItem(pattern_name)

        # Connect load pattern button to method
        self.ui.loadButton.clicked.connect(lambda: self.load_pattern(self.patterns))

    def load_pattern(self, patterns):
        """
        Load the selected pattern and emit the patternSelected signal.

        Args:
            patterns (dict): Dictionary containing available patterns.
        """
        # Select pattern name in the list
        selected_pattern = self.ui.patternsListWidget.currentItem().text()
        if selected_pattern in patterns:
            # Select pattern data and emit to MainWindow
            pattern = patterns[selected_pattern]
            self.patternSelected.emit(pattern)
        else:
            QMessageBox.warning(self, "Invalid Pattern", "Pattern not found.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    width = 30
    height = 30
    board = Board(np.array([[Cell(x, y, 0, 0) for x in range(width)] for y in range(height)], dtype=object))
    window = MainWindow(board)
    window.show()
    sys.exit(app.exec_())
