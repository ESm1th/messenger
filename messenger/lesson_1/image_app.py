import sys

from PIL import (
    Image,
    ImageDraw,
)
from PIL.ImageQt import ImageQt

from PyQt5.QtWidgets import (
    QApplication,
    QDesktopWidget,
    QWidget,
    QPushButton,
    QLabel,
    QGroupBox,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImageFilter(QWidget):

    def __init__(self, *args, **kwargs):

        super().__init__()
        self.init_ui()

    def init_ui(self):
        btn_size = (120, 40)

        button = QPushButton('Choose image')
        button.setFixedSize(*btn_size)
        button.clicked.connect(self.open_file)

        default_button = QPushButton('Default image')
        default_button.setFixedSize(*btn_size)
        default_button.clicked.connect(self.to_default)
        default_button.setDisabled(True)

        self.grayscale_btn = QPushButton('Grayscale')
        self.grayscale_btn.setFixedSize(*btn_size)
        self.grayscale_btn.clicked.connect(self.grayscale)
        self.grayscale_btn.setDisabled(True)

        self.sepia_btn = QPushButton('Sepia')
        self.sepia_btn.setFixedSize(*btn_size)
        self.sepia_btn.clicked.connect(self.sepia)
        self.sepia_btn.setDisabled(True)

        self.negative_btn = QPushButton('Negative')
        self.negative_btn.setFixedSize(*btn_size)
        self.negative_btn.clicked.connect(self.negative)
        self.negative_btn.setDisabled(True)

        self.black_and_white_btn = QPushButton('B and W')
        self.black_and_white_btn.setFixedSize(*btn_size)
        self.black_and_white_btn.clicked.connect(self.black_and_white)
        self.black_and_white_btn.setDisabled(True)

        h_buttons_layout = QHBoxLayout()
        h_buttons_layout.setAlignment(Qt.AlignHCenter)
        h_buttons_layout.addWidget(button)
        h_buttons_layout.addWidget(self.grayscale_btn)
        h_buttons_layout.addWidget(self.sepia_btn)
        h_buttons_layout.addWidget(self.negative_btn)
        h_buttons_layout.addWidget(self.black_and_white_btn)
        h_buttons_layout.addWidget(default_button)

        self.image_label = QLabel()
        self.image_label.setFixedSize(300, 300)
        self.image_label.setScaledContents(True)

        v_img_layout = QVBoxLayout()
        v_img_layout.addWidget(self.image_label)
        v_img_layout.setAlignment(Qt.AlignCenter)

        image_box = QGroupBox('Image')
        image_box.setLayout(v_img_layout)

        v_main_layout = QVBoxLayout()
        v_main_layout.addWidget(image_box)
        v_main_layout.addLayout(h_buttons_layout)

        self.setLayout(v_main_layout)
        self.setFixedWidth(800)
        self.setFixedHeight(450)
        self.setWindowTitle('Change image style')
        self.to_center()
        self.show()

    def to_center(self):
        """
        Gets geometry of app window, positions it on the center of the screen
        and then moves app window to it
        """

        rectangle = self.frameGeometry()
        desktop_center = QDesktopWidget().availableGeometry().center()
        rectangle.moveCenter(desktop_center)
        self.move(rectangle.topLeft())

    def open_file(self):

        self.image = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]
        self.to_default()

        buttons = self.findChildren(QPushButton)
        for button in buttons:
            button.setDisabled(False)

    def to_default(self):
        if hasattr(self, 'image'):
            pixmap = QPixmap(self.image)
            self.image_label.setPixmap(pixmap)

    def grayscale(self):
        if hasattr(self, 'image'):
            pixmap = ImageProcessor(self.image).grayscale_pixmap()
            self.image_label.setPixmap(pixmap)

    def sepia(self):
        if hasattr(self, 'image'):
            pixmap = ImageProcessor(self.image).sepia_pixmap()
            self.image_label.setPixmap(pixmap)

    def negative(self):
        if hasattr(self, 'image'):
            pixmap = ImageProcessor(self.image).negative_pixmap()
            self.image_label.setPixmap(pixmap)

    def black_and_white(self):
        if hasattr(self, 'image'):
            pixmap = ImageProcessor(self.image).black_and_white_pixmap()
            self.image_label.setPixmap(pixmap)


class ImageProcessor:

    def __init__(self, path):
        self.image = Image.open(path)
        self.setup()

    def setup(self):
        self.draw = ImageDraw.Draw(self.image)
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.pix = self.image.load()

    def grayscale_pixmap(self):

        for i in range(self.width):

            for j in range(self.height):

                a = self.pix[i, j][0]
                b = self.pix[i, j][1]
                c = self.pix[i, j][2]
                S = (a + b + c)
                self.draw.point((i, j), (S, S, S))

        img = ImageQt(self.image.convert('RGBA'))
        pixmap = QPixmap.fromImage(img)
        return pixmap

    def sepia_pixmap(self):
        depth = 30

        for i in range(self.width):

            for j in range(self.height):

                a = self.pix[i, j][0]
                b = self.pix[i, j][1]
                c = self.pix[i, j][2]
                S = (a + b + c)
                a = S + depth * 2
                b = S + depth
                c = S
                if (a > 255):
                    a = 255
                if (b > 255):
                    b = 255
                if (c > 255):
                    c = 255
                self.draw.point((i, j), (a, b, c))

        img = ImageQt(self.image.convert('RGBA'))
        pixmap = QPixmap.fromImage(img)
        return pixmap

    def negative_pixmap(self):

        for i in range(self.width):

            for j in range(self.height):

                a = self.pix[i, j][0]
                b = self.pix[i, j][1]
                c = self.pix[i, j][2]
                self.draw.point((i, j), (255 - a, 255 - b, 255 - c))

        img = ImageQt(self.image.convert('RGBA'))
        pixmap = QPixmap.fromImage(img)
        return pixmap

    def black_and_white_pixmap(self):
        factor = 50

        for i in range(self.width):

            for j in range(self.height):

                a = self.pix[i, j][0]
                b = self.pix[i, j][1]
                c = self.pix[i, j][2]
                S = a + b + c

                if (S > (((255 + factor) // 2) * 3)):
                    a, b, c = 255, 255, 255
                else:
                    a, b, c = 0, 0, 0

                self.draw.point((i, j), (a, b, c))

        img = ImageQt(self.image.convert('RGBA'))
        pixmap = QPixmap.fromImage(img)
        return pixmap


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = ImageFilter()
    sys.exit(app.exec_())
