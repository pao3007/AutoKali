from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from SensAcc.MyMainWindow import MyMainWindow


class FiguresWindow(QMainWindow):

    def __init__(self, parent_window: MyMainWindow):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("Calibration figures")
        self.widget = QWidget()
        self.layout = QVBoxLayout()

    def init_ui(self, data):
        self.clear_layout(self.layout)

        opt_sentinel_file_name = self.parent_window.autoCalib.opt_sentinel_file_name
        title_font_size = 12
        label_font_size = 16

        fig1 = Figure()
        canvas1 = FigureCanvas(fig1)
        ax1 = fig1.add_subplot(111)
        ax1.plot(data[1], data[2], label='Optical')
        ax1.plot(data[3], data[4], label='Reference')
        ax1.legend()
        ax1.title('Resampled and resized data of ' + opt_sentinel_file_name, fontsize=title_font_size)
        ax1.ylabel('Acceleration [g]', fontsize=label_font_size)
        ax1.xlabel('Time[s]', fontsize=label_font_size)
        ax1.grid(which='both')
        ax1.minorticks_on()
        self.layout.addWidget(canvas1)

        fig2 = Figure()
        canvas2 = FigureCanvas(fig2)
        ax2 = fig2.add_subplot(111)
        ax2.plot(data[5], data[6], label='Optical')
        ax2.plot(data[7], data[8], label='Reference')
        ax2.legend()
        ax2.title('Spectrum of ' + opt_sentinel_file_name, fontsize=title_font_size)
        ax2.ylabel('Spectral Density [dB]', fontsize=label_font_size)
        ax2.xlabel('Frequency [Hz]', fontsize=label_font_size)
        ax2.grid(which='both')
        ax2.minorticks_on()
        self.layout.addWidget(canvas2)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.move_to_side()

    def move_to_side(self):
        main_window_geom = self.parent_window.geometry()
        self.setGeometry(main_window_geom.x() + main_window_geom.width(), main_window_geom.y(),
                         self.geometry().width(), self.geometry().height())

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
            layout.removeItem(layout.itemAt(i))
