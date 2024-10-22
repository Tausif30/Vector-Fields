#pyinstaller --onefile --windowed --icon=Logo.ico Vector-Fields.py

import sys
import numpy as np
import sympy as sp
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QComboBox, QLineEdit, QRadioButton, QButtonGroup, QFileDialog, QFormLayout, QMessageBox
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

epsilon = 1e-5


def safe_normalize(U, V, W=None):
    if W is None:  # 2D case
        norm = np.sqrt(U ** 2 + V ** 2)
        norm = np.where(norm < 1e-2, 1e-2, norm)
        return U / norm, V / norm
    else:  # 3D case
        norm = np.sqrt(U ** 2 + V ** 2 + W ** 2) + epsilon
        norm = np.where(norm < 1e-2, 1e-2, norm)
        return U / norm, V / norm, W / norm


class VectorFieldVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vector Field Plotter")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon('Logo.ico'))

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        control_panel.setFixedWidth(300)

        coord_label = QLabel("Coordinate System:")
        coord_label.setStyleSheet("font-size: 20px;")
        self.coord_combo = QComboBox()
        self.coord_combo.addItems(["Cartesian", "Cylindrical", "Spherical"])
        self.coord_combo.setStyleSheet(
            "font-size: 20px; padding: 5px 15px 5px 15px; margin-bottom: 12px; border-radius: 18px; outline: none;")
        self.coord_combo.currentIndexChanged.connect(self.update_input_fields)

        vector_label = QLabel("Vector Field:")
        vector_label.setStyleSheet("font-size: 20px; margin-top: auto")
        self.vector_entries = QWidget()
        self.vector_layout = QFormLayout()
        self.vector_entries.setLayout(self.vector_layout)
        self.entry1 = QLineEdit()
        self.entry2 = QLineEdit()
        self.entry3 = QLineEdit()
        self.entry1.setStyleSheet("font-size: 20px; padding: 5px 15px 5px 15px; border-radius: 18px;")
        self.entry2.setStyleSheet("font-size: 20px; padding: 5px 15px 5px 15px; border-radius: 18px;")
        self.entry3.setStyleSheet("font-size: 20px; padding: 5px 15px 5px 15px; border-radius: 18px;")

        self.plot_type_group = QButtonGroup()
        self.plot_type_label = QLabel("Plot Type:")
        self.plot_type_label.setStyleSheet("font-size: 20px;")
        self.plot_type_widgets = QWidget()
        self.plot_type_layout = QVBoxLayout()
        self.plot_type_widgets.setLayout(self.plot_type_layout)

        plot_button = QPushButton("Plot")
        plot_button.clicked.connect(self.plot_vector_field)
        save_button = QPushButton("Save Plot")
        save_button.clicked.connect(self.save_plot)

        self.move_button = QPushButton("Move")
        self.zoom_button = QPushButton("Zoom")
        self.rotate_button = QPushButton("Rotate")
        self.edit_axis_button = QPushButton("Edit Axis")
        self.reset_button = QPushButton("Reset View")

        self.move_button.clicked.connect(lambda: self.set_navigation_mode('move'))
        self.zoom_button.clicked.connect(lambda: self.set_navigation_mode('zoom'))
        self.rotate_button.clicked.connect(lambda: self.set_navigation_mode('rotate'))
        self.edit_axis_button.clicked.connect(lambda: self.set_navigation_mode('edit_axis'))
        self.reset_button.clicked.connect(self.reset_view)
        self.current_mode = None

        control_layout.addWidget(coord_label)
        control_layout.addWidget(self.coord_combo)
        control_layout.addWidget(vector_label)
        control_layout.addWidget(self.vector_entries)
        control_layout.addWidget(self.plot_type_label)
        control_layout.addWidget(self.plot_type_widgets)
        control_layout.addWidget(plot_button)
        control_layout.addWidget(save_button)
        control_layout.addWidget(self.move_button)
        control_layout.addWidget(self.zoom_button)
        control_layout.addWidget(self.rotate_button)
        control_layout.addWidget(self.edit_axis_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addStretch()

        self.plot_widget = QWidget()
        self.plot_layout = QVBoxLayout()
        self.plot_widget.setLayout(self.plot_layout)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.plot_widget)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()
        self.plot_layout.addWidget(self.canvas)

        self.update_input_fields()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)

        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QWidget {
                background-color: #353535;
                color: white;
                font-size: 16px;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid whitesmoke;
                padding: 8px;
                border-radius: 15px;
            }
            QPushButton:hover, QPushButton:focus {
                background-color: whitesmoke;
                color: #4a4a4a;
            }
            QLineEdit, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid whitesmoke;
                padding: 5px;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                color: whitesmoke;
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 30px;
                border-left-width: 1px;
                border-left-color: whitesmoke;
                border-left-style: solid;
            }
            QComboBox::down-arrow {
                width: 15px;
                height: 15px;
                border-radius: 7px;
                margin-right: 2px;
                color: whitesmoke;
                background-color: whitesmoke;
            }
            QRadioButton {
                spacing: 5px;
                padding: 5px; 
                border: solid 2px whitesmoke;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
                border-radius: 12px;
                padding: 3px;
                border: solid 2px whitesmoke;
            }
            QRadioButton::indicator:checked {
                background-color: #4a90e2;
                border: 2px solid whitesmoke;
            }
        """)

    def update_input_fields(self):
        coord_system = self.coord_combo.currentText()

        for i in reversed(range(self.plot_type_layout.count())):
            self.plot_type_layout.itemAt(i).widget().setParent(None)

        for i in reversed(range(self.vector_layout.count())):
            self.vector_layout.itemAt(i).widget().setParent(None)

        if coord_system == "Cartesian":
            plot_types = ["3D", "XY", "YZ", "XZ"]
            labels = ["Vx:", "Vy:", "Vz:"]
            placeholders = ["y", "-x", "z"]
        elif coord_system == "Cylindrical":
            plot_types = ["3D", "Rθ", "RZ", "θZ"]
            labels = ["Vr:", "Vθ:", "Vz:"]
            placeholders = ["-r*sin(theta)", "r*cos(theta)", "z"]
        else:  # Spherical
            plot_types = ["3D", "Rθ", "Rφ", "θφ"]
            labels = ["Vr:", "Vθ:", "Vφ:"]
            placeholders = ["r*sin(theta)*cos(phi)", "r*sin(theta)*sin(phi)", "r*cos(theta)"]

        for plot_type in plot_types:
            radio = QRadioButton(plot_type)
            self.plot_type_group.addButton(radio)
            self.plot_type_layout.addWidget(radio)
            radio.setStyleSheet("""
                QRadioButton {
                    spacing: 5px;
                    padding: 5px;
                }
                QRadioButton::indicator {
                    width: 15px;
                    height: 15px;
                    border-radius: 12px;
                    border: 2px solid whitesmoke;
                }
                QRadioButton::indicator:checked {
                    background-color: #4a90e2;
                    border: 2px solid whitesmoke;
                }
            """)

        self.plot_type_group.buttons()[0].setChecked(True)

        self.entry1.setPlaceholderText(placeholders[0])
        self.entry2.setPlaceholderText(placeholders[1])
        self.entry3.setPlaceholderText(placeholders[2])

        self.vector_layout.addRow(labels[0], self.entry1)
        self.vector_layout.addRow(labels[1], self.entry2)
        self.vector_layout.addRow(labels[2], self.entry3)

    def plot_vector_field(self):
        try:
            if (self.current_mode == 'move'):
                self.toolbar.pan()
            if (self.current_mode == 'zoom'):
                self.toolbar.zoom()
            self.current_mode = 'plot'
            coord_system = self.coord_combo.currentText()
            plot_type = self.plot_type_group.checkedButton().text()
            vector_field = [self.entry1.text() or self.entry1.placeholderText(),
                            self.entry2.text() or self.entry2.placeholderText(),
                            self.entry3.text() or self.entry3.placeholderText()]

            self.figure.clear()

            if plot_type == "3D":
                ax = self.figure.add_subplot(111, projection='3d')
                is_3D = True
            else:
                ax = self.figure.add_subplot(111)
                is_3D = False

            if coord_system == "Cartesian":
                self.plot_cartesian(ax, vector_field, plot_type)
            elif coord_system == "Cylindrical":
                self.plot_cylindrical(ax, vector_field, plot_type)
            else:  # Spherical
                self.plot_spherical(ax, vector_field, plot_type)

            if is_3D:
                self.figure.tight_layout()
            else:
                ax.set_position([0.1, 0.1, 0.85, 0.85])
                ax.grid(True)

            self.canvas.draw()
        except Exception as e:
            self.show_error_message(str(e))

    def show_error_message(self, error_message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Error in equation")
        msg.setInformativeText(f"An error occurred while processing the equation. Please correct the equation and try again.")
        msg.setWindowTitle("Equation Error")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    def plot_cartesian(self, ax, vector_field, plot_type):
        try:
            x, y, z = sp.symbols('x y z')
            Fx, Fy, Fz = sp.sympify(vector_field)
            Fx = Fx.subs({x: x + 1e-5, y: y + 1e-6, z: z + 1e-7})
            Fy = Fy.subs({x: x + 1e-5, y: y + 1e-6, z: z + 1e-7})
            Fz = Fz.subs({x: x + 1e-5, y: y + 1e-6, z: z + 1e-7})

            title = f"Vector Field: ({Fx}, {Fy}, {Fz})"
            if plot_type != "3D":
                ax.set_aspect('equal', adjustable='box')

            if plot_type == "3D":
                X, Y, Z = np.meshgrid(np.linspace(-10, 10, 8),
                                      np.linspace(-10, 10, 8),
                                      np.linspace(-10, 10, 8))

                U = sp.lambdify((x, y, z), Fx)(X, Y, Z)
                V = sp.lambdify((x, y, z), Fy)(X, Y, Z)
                W = sp.lambdify((x, y, z), Fz)(X, Y, Z)

                U, V, W = safe_normalize(U, V, W)

                ax.quiver(X, Y, Z, U, V, W, length=1, normalize=False, linewidth=2)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)
                ax.set_zlim(-10, 10)
            elif plot_type == "XY":
                X, Y = np.meshgrid(np.linspace(-10, 10, 20), np.linspace(-10, 10, 20))
                U = sp.lambdify((x, y), Fx.subs(z, 0))(X, Y)
                V = sp.lambdify((x, y), Fy.subs(z, 0))(X, Y)
                U, V = safe_normalize(U, V)
                ax.quiver(X, Y, U, V)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)
            elif plot_type == "YZ":
                Y, Z = np.meshgrid(np.linspace(-10, 10, 20), np.linspace(-10, 10, 20))
                V = sp.lambdify((y, z), Fy.subs(x, 0))(Y, Z)
                W = sp.lambdify((y, z), Fz.subs(x, 0))(Y, Z)
                V, W = safe_normalize(V, W)
                ax.quiver(Y, Z, V, W)
                ax.set_xlabel('Y')
                ax.set_ylabel('Z')
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)
            elif plot_type == "XZ":
                X, Z = np.meshgrid(np.linspace(-10, 10, 20), np.linspace(-10, 10, 20))
                U = sp.lambdify((x, z), Fx.subs(y, 0))(X, Z)
                W = sp.lambdify((x, z), Fz.subs(y, 0))(X, Z)
                U, W = safe_normalize(U, W)
                ax.quiver(X, Z, U, W)
                ax.set_xlabel('X')
                ax.set_ylabel('Z')
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)
        except Exception as e:
            raise ValueError(f"Error in Cartesian equation: {str(e)}")

    def plot_cylindrical(self, ax, vector_field, plot_type):
        try:
            r, theta, z = sp.symbols('r theta z')
            Fr, Ftheta, Fz = sp.sympify(vector_field)
            Fr = Fr.subs({r: r + 1e-5, z: z + 1e-6})
            Ftheta = Ftheta.subs({r: r + 1e-5, z: z + 1e-6})
            Fz = Fz.subs({r: r + 1e-6, z: z + 1e-6})

            title = f"Vector Field: ({Fr}, {Ftheta}, {Fz})"

            if plot_type != "3D":
                ax.set_aspect('equal', adjustable='box')

            if plot_type == "3D":
                R, THETA, Z = np.meshgrid(np.linspace(0, 10, 8),
                                          np.linspace(0, 2 * np.pi, 16),
                                          np.linspace(-10, 10, 8))
                X = R * np.cos(THETA)
                Y = R * np.sin(THETA)

                U = sp.lambdify((r, theta, z), Fr)(R, THETA, Z) * np.cos(THETA) - \
                    sp.lambdify((r, theta, z), Ftheta)(R, THETA, Z) * np.sin(THETA)
                V = sp.lambdify((r, theta, z), Fr)(R, THETA, Z) * np.sin(THETA) + \
                    sp.lambdify((r, theta, z), Ftheta)(R, THETA, Z) * np.cos(THETA)
                W = sp.lambdify((r, theta, z), Fz)(R, THETA, Z)

                U, V, W = safe_normalize(U, V, W)

                ax.quiver(X, Y, Z, U, V, W, length=1, normalize=False, linewidth=2)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)
                ax.set_zlim(-10, 10)
            elif plot_type == "Rθ":
                R, THETA = np.meshgrid(np.linspace(0, 10, 20), np.linspace(0, 2 * np.pi, 20))
                U = sp.lambdify((r, theta), Fr.subs(z, 0))(R, THETA)
                V = sp.lambdify((r, theta), Ftheta.subs(z, 0))(R, THETA)
                U, V = safe_normalize(U, V)
                ax.quiver(R, THETA, U, V, angles='xy', scale_units='xy', scale=5)
                ax.set_xlabel('R')
                ax.set_ylabel('θ')
                ax.set_xlim(0, 10)
                ax.set_ylim(0, 2 * np.pi)
            elif plot_type == "RZ":
                R, Z = np.meshgrid(np.linspace(0, 10, 20), np.linspace(-10, 10, 20))
                U = sp.lambdify((r, z), Fr.subs(theta, 0))(R, Z)
                W = sp.lambdify((r, z), Fz.subs(theta, 0))(R, Z)
                U, W = safe_normalize(U, W)
                ax.quiver(R, Z, U, W)
                ax.set_xlabel('R')
                ax.set_ylabel('Z')
                ax.set_xlim(0, 10)
                ax.set_ylim(-10, 10)
            elif plot_type == "θZ":
                THETA, Z = np.meshgrid(np.linspace(0, 2 * np.pi, 20), np.linspace(-10, 10, 20))
                V = sp.lambdify((theta, z), Ftheta.subs(r, 5))(THETA, Z)
                W = sp.lambdify((theta, z), Fz.subs(r, 5))(THETA, Z)
                V, W = safe_normalize(V, W)
                ax.quiver(THETA, Z, V, W)
                ax.set_xlabel('θ')
                ax.set_ylabel('Z')
                ax.set_xlim(0, 2 * np.pi)
                ax.set_ylim(-10, 10)
        except Exception as e:
            raise ValueError(f"Error in Cylindrical equation: {str(e)}")

    def plot_spherical(self, ax, vector_field, plot_type):
        try:
            r, theta, phi = sp.symbols('r theta phi')
            Fr, Ftheta, Fphi = sp.sympify(vector_field)

            title = f"Vector Field: ({Fr}, {Ftheta}, {Fphi})"

            if plot_type != "3D":
                ax.set_aspect('equal', adjustable='box')

            if plot_type == "3D":
                R, THETA, PHI = np.meshgrid(np.linspace(0, 10, 8),
                                            np.linspace(0, np.pi, 8),
                                            np.linspace(0, 2 * np.pi, 16))

                X = R * np.sin(THETA) * np.cos(PHI)
                Y = R * np.sin(THETA) * np.sin(PHI)
                Z = R * np.cos(THETA)

                U = sp.lambdify((r, theta, phi), Fr)(R, THETA, PHI) * np.sin(THETA) * np.cos(PHI) + \
                    sp.lambdify((r, theta, phi), Ftheta)(R, THETA, PHI) * np.cos(THETA) * np.cos(PHI) - \
                    sp.lambdify((r, theta, phi), Fphi)(R, THETA, PHI) * np.sin(PHI)
                V = sp.lambdify((r, theta, phi), Fr)(R, THETA, PHI) * np.sin(THETA) * np.sin(PHI) + \
                    sp.lambdify((r, theta, phi), Ftheta)(R, THETA, PHI) * np.cos(THETA) * np.sin(PHI) + \
                    sp.lambdify((r, theta, phi), Fphi)(R, THETA, PHI) * np.cos(PHI)
                W = sp.lambdify((r, theta, phi), Fr)(R, THETA, PHI) * np.cos(THETA) - \
                    sp.lambdify((r, theta, phi), Ftheta)(R, THETA, PHI) * np.sin(THETA)

                U, V, W = safe_normalize(U, V, W)

                ax.quiver(X, Y, Z, U, V, W, length=1, normalize=False, linewidth=2)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)
                ax.set_zlim(-10, 10)
            elif plot_type == "Rθ":
                R, THETA = np.meshgrid(np.linspace(0, 10, 20), np.linspace(0, np.pi, 20))
                U = sp.lambdify((r, theta), Fr.subs(phi, 0))(R, THETA)
                V = sp.lambdify((r, theta), Ftheta.subs(phi, 0))(R, THETA)
                U, V = safe_normalize(U, V)
                ax.quiver(R, THETA, U, V, angles='xy', scale_units='xy', scale=5)
                ax.set_xlabel('R')
                ax.set_ylabel('θ')
                ax.set_xlim(0, 10)
                ax.set_ylim(0, np.pi)
            elif plot_type == "Rφ":
                R, PHI = np.meshgrid(np.linspace(0, 10, 20), np.linspace(0, 2 * np.pi, 20))
                U = sp.lambdify((r, phi), Fr.subs(theta, np.pi / 2))(R, PHI)
                W = sp.lambdify((r, phi), Fphi.subs(theta, np.pi / 2))(R, PHI)
                U, W = safe_normalize(U, W)
                ax.quiver(R, PHI, U, W)
                ax.set_xlabel('R')
                ax.set_ylabel('φ')
                ax.set_xlim(0, 10)
                ax.set_ylim(0, 2 * np.pi)
            elif plot_type == "θφ":
                THETA, PHI = np.meshgrid(np.linspace(0, np.pi, 20), np.linspace(0, 2 * np.pi, 20))
                V = sp.lambdify((theta, phi), Ftheta.subs(r, 5))(THETA, PHI)
                W = sp.lambdify((theta, phi), Fphi.subs(r, 5))(THETA, PHI)
                V, W = safe_normalize(V, W)
                ax.quiver(THETA, PHI, V, W)
                ax.set_xlabel('θ')
                ax.set_ylabel('φ')
                ax.set_xlim(0, np.pi)
                ax.set_ylim(0, 2 * np.pi)
        except Exception as e:
            raise ValueError(f"Error in Spherical equation: {str(e)}")

    def save_plot(self):
        if (self.current_mode == 'move'):
            self.toolbar.pan()
        if (self.current_mode == 'zoom'):
            self.toolbar.zoom()
        self.current_mode = 'edit_axis'
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            self.figure.savefig(file_path)

    def set_navigation_mode(self, mode):
        if hasattr(self, 'toolbar'):
            if mode == 'move':
                self.toolbar.pan()
                self.current_mode = 'move'
            elif mode == 'zoom':
                self.toolbar.zoom()
                self.current_mode = 'zoom'
            elif mode == 'rotate':
                self.canvas.mpl_connect('motion_notify_event', self.rotate_view)
                if (self.current_mode == 'move'):
                    self.toolbar.pan()
                if (self.current_mode == 'zoom'):
                    self.toolbar.zoom()
                self.current_mode = 'rotate'
            elif mode == 'edit_axis':
                self.toolbar.edit_parameters()
                if (self.current_mode == 'move'):
                    self.toolbar.pan()
                if (self.current_mode == 'zoom'):
                    self.toolbar.zoom()
                self.current_mode = 'edit_axis'

    def rotate_view(self, event):
        if event.button is not None and isinstance(self.figure.gca(), Axes3D):
            ax = self.figure.gca()
            ax.view_init(elev=ax.elev + (event.ydata - event.lasty),
                         azim=ax.azim + (event.xdata - event.lastx))
            self.canvas.draw()

    def reset_view(self):
        if hasattr(self, 'toolbar'):
            if (self.current_mode == 'move'):
                self.toolbar.pan()
            if (self.current_mode == 'zoom'):
                self.toolbar.zoom()
            self.current_mode = 'reset_view'
            self.toolbar.home()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VectorFieldVisualizer()
    window.show()
    sys.exit(app.exec_())