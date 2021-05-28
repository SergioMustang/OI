import copy
import json
import os
import re
from os import listdir

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QHBoxLayout, \
    QComboBox, QInputDialog, QLabel
from PyQt5.QtGui import QPixmap, QIcon
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from PyQt5.QtWinExtras import QWinTaskbarButton


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    mask_flag = False

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(0)
        alpha = 0.4
        while self._run_flag:

            ret, cv_img = cap.read()
            cv_img_2 = copy.deepcopy(cv_img)
            if ret and a.mouse_Is_Moving and a.left_Button_Moved:
                cv_img = self.frame_live_drawing(cv_img, cv_img_2, alpha)
            if self.mask_flag:
                mask = self.draw_mask()
                cv_img = self.apply_mask(cv_img, mask)
                if a.imageIsZoomed:
                    cv_img = self.zoomed_img(cv_img_2)
            else:
                cv_img = self.draw_polygon(cv_img, cv_img_2, alpha)
                if a.imageIsZoomed:
                    cv_img = self.zoomed_img(cv_img_2)
            self.textLabelUpdate()
            self.change_pixmap_signal.emit(cv_img)
        cap.release()

    @staticmethod
    def frame_live_drawing(cv_img, cv_img_2, alpha):
        i = len(a.cords_list) - 2
        if i >= 0:
            cv2.rectangle(cv_img_2, (a.cords_list[i], a.cords_list[i + 1]),
                          (a.lastXtrackingPos, a.lastYtrackingPos), (0, 255, 0), 2)
            cv_img = cv2.addWeighted(cv_img, alpha, cv_img_2, 1 - alpha, 0)
        return cv_img

    @staticmethod
    def frame_stoped_drawing(cv_img_2, alpha):
        holder_img = copy.deepcopy(cv_img_2)
        i = int(len(a.cords_list) - 2)
        if i >= 0 and a.mouseTrackingIsSafe:
            cv2.rectangle(holder_img, (a.cords_list[i], a.cords_list[i + 1]),
                          (a.lastXtrackingPos, a.lastYtrackingPos), (0, 255, 0), 2)
            holder_img = cv2.addWeighted(holder_img, alpha, cv_img_2, 1 - alpha, 0)
        return holder_img

    @staticmethod
    def draw_polygon(cv_img, cv_img_2, alpha):
        i = int(len(a.cords_list) / 4)
        if i == 0:
            pass
        else:
            for i in range(i):
                blue = 0
                if i == a.currentAppertureNumber - 1:
                    blue = 255
                cv2.rectangle(cv_img, (a.cords_list[0 + (i * 4)], a.cords_list[1 + (i * 4)]),
                              (a.cords_list[2 + (i * 4)], a.cords_list[3 + (i * 4)]), (blue, 255, 0), -1)
        cv_img = cv2.addWeighted(cv_img, alpha, cv_img_2, 1 - alpha, 0)
        return cv_img

    @staticmethod
    def draw_mask():
        i = int(len(a.cords_list) / 4)
        if i == 0:
            mask = np.zeros((a.camera_image_height, a.camera_image_width, 1), np.uint8)
        else:
            mask = np.zeros((a.camera_image_height, a.camera_image_width, 1), np.uint8)
            for i in range(i):
                cv2.rectangle(mask, (a.cords_list[0 + (i * 4)], a.cords_list[1 + (i * 4)]),
                              (a.cords_list[2 + (i * 4)], a.cords_list[3 + (i * 4)]), (255, 255, 255), -1)
        return mask

    @staticmethod
    def apply_mask(cv_img, mask):
        cv_img = cv2.bitwise_and(cv_img, cv_img, mask=mask)
        return cv_img

    @staticmethod
    def zoomed_img(cv_img):
        i = a.currentAppertureNumber
        if a.apertureNumber == 0:
            return cv_img
        else:
            i = i - 1
            x1 = a.cords_list[0 + (i * 4)]
            x2 = a.cords_list[2 + (i * 4)]
            y1 = a.cords_list[1 + (i * 4)]
            y2 = a.cords_list[3 + (i * 4)]
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1
            cropped = cv_img[y1:y2, x1:x2]
            return cropped

    def textLabelUpdate(self):
        textForLabel = str(a.currentAppertureNumber) + str(" из ") + str(int(len(a.cords_list) / 4))
        a.aperture_text.setText(textForLabel)
        if int(len(a.cords_list) / 4) == 0:
            a.aperture_text.setText(" ")

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.cap = cv2.VideoCapture(0)
        self.camera_image_width = int(self.cap.get(3))
        self.camera_image_height = int(self.cap.get(4))
        self.cap.release()

        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowTitle("Visual Inspection")

        self.mask_is_new_flag = True
        self.mask_name = None
        self.mouse_Is_Moving = False
        self.left_Button_Moved = False
        self.apertureNumber = 0
        self.currentAppertureNumber = 1
        self.cords_list = []
        self.mouseTrackingIsSafe = False
        self.imageIsZoomed = False
        self.lastXtrackingPos = None
        self.lastYtrackingPos = None

        # create the label that holds the image
        self.image_label = GraphicsView()
        self.image_label.setAlignment(Qt.AlignTop)
        self.image_label.setCursor(QtCore.Qt.CrossCursor)
        hbox = QHBoxLayout(self)
        vbox = QVBoxLayout()

        self.aperture_text = QLabel()
        self.aperture_text.setFont(QtGui.QFont("Times", 20, QtGui.QFont.Bold))


        self.sizeFixer = QWidget(self)
        self.sizeFixer.setMaximumSize(500, 500)

        self.masks_list = QComboBox(self)
        self.masks_list.addItems(["Создать новую маску"])
        self.masks_list.setFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold))

        isdir = os.path.isdir("./Masks")

        if isdir:
            dir_listing = listdir("./Masks")
        else:
            os.mkdir("./Masks")
            dir_listing = listdir("./Masks")
        for file in dir_listing:
            file = re.sub(r".txt", "", file)
            self.masks_list.addItems([file])

        self.masks_list.setMinimumSize(300, 30)
        maskButton = QPushButton(" Наложить маску ")
        maskButton.setCheckable(True)
        maskButton.setFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold))
        zoomButton = QPushButton(" Приблизить ")
        zoomButton.setCheckable(True)
        zoomButton.setFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold))
        leftArrow = QPushButton(" ← ")
        leftArrow.setFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold))
        rightArrow = QPushButton(" → ")
        rightArrow.setFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold))
        saveMaskButton = QPushButton(" Сохранить маску ")
        saveMaskButton.setFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold))

        maskButton.setMaximumSize(200, 30)
        zoomButton.setMaximumSize(200, 30)
        leftArrow.setMaximumSize(100, 30)
        rightArrow.setMaximumSize(100, 30)
        saveMaskButton.setMaximumSize(200, 30)

        maskButton.clicked[bool].connect(self.showMask)
        zoomButton.clicked[bool].connect(self.zoomAction)
        leftArrow.clicked[bool].connect(self.leftArrowAction)
        rightArrow.clicked[bool].connect(self.rightArrowAction)
        self.masks_list.activated[str].connect(self.masks_list_activated)
        saveMaskButton.clicked[bool].connect(self.saveMask)

        vbox2 = QVBoxLayout()

        vbox2.addWidget(self.masks_list, alignment=Qt.AlignCenter)
        vbox2.addWidget(maskButton, alignment=Qt.AlignCenter)
        vbox2.addWidget(zoomButton, alignment=Qt.AlignCenter)
        vbox2.addWidget(saveMaskButton, alignment=Qt.AlignCenter)
        vbox2.addWidget(self.aperture_text, alignment=Qt.AlignCenter)

        hbox2 = QHBoxLayout(self)
        hbox2.addWidget(leftArrow, alignment=Qt.AlignCenter)
        hbox2.addWidget(rightArrow, alignment=Qt.AlignCenter)
        vbox2.addLayout(hbox2)

        self.sizeFixer.setLayout(vbox2)

        # create a vertical box layout and add the two labels

        vbox.addWidget(self.image_label)

        hbox.addLayout(vbox)
        hbox.addWidget(self.sizeFixer, alignment=Qt.AlignRight)

        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)

        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    def showMask(self, pressed):
        source = self.sender()
        if pressed:
            source.setText(" Убрать маску ")
            self.thread.mask_flag = True
        else:
            source.setText(" Наложить маску ")
            self.thread.mask_flag = False

    def masks_list_activated(self, text):
        if text != "Создать новую маску":
            self.mask_is_new_flag = False
            self.imageIsZoomed = False
            self.cords_list.clear()
            with open('./Masks/'+text + '.txt', 'r') as filehandle:
                self.cords_list = json.load(filehandle)
                self.apertureNumber = int(len(a.cords_list) / 4)
                if self.apertureNumber != 0:
                    self.currentAppertureNumber = 1
            self.mask_name = text
        else:
            self.currentAppertureNumber = 1
            self.mask_is_new_flag = True
            self.cords_list.clear()

    def zoomAction(self, pressed):
        source = self.sender()
        if pressed:
            source.setText(" Отдалить ")
            self.imageIsZoomed = True
        else:
            source.setText(" Приблизить ")
            self.imageIsZoomed = False

    def leftArrowAction(self):
        self.apertureNumber = int(len(a.cords_list) / 4)
        if self.apertureNumber >= 1:
            if self.currentAppertureNumber == 1:
                self.currentAppertureNumber = self.apertureNumber
            else:
                self.currentAppertureNumber = self.currentAppertureNumber - 1

    def rightArrowAction(self):
        self.apertureNumber = int(len(a.cords_list) / 4)
        if self.apertureNumber >= 1:
            if self.currentAppertureNumber == self.apertureNumber:
                self.currentAppertureNumber = 1
            else:
                self.currentAppertureNumber = self.currentAppertureNumber + 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A:
            self.leftArrowAction()
        elif event.key() == Qt.Key_D:
            self.rightArrowAction()

    def saveMask(self):
        if self.mask_is_new_flag:
            text, ok = QInputDialog.getText(self, 'Сохранение новой маски',
                                            'Введите название платы:')
            if ok:
                with open('./Masks/'+text + '.txt', 'w') as filehandle:
                    json.dump(self.cords_list, filehandle)
                self.mask_is_new_flag = False
                self.masks_list.addItems([text])
            else:
                pass
        else:
            with open('./Masks/' + self.mask_name + '.txt', 'w') as filehandle:
                json.dump(self.cords_list, filehandle)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
        self.image_label.resizeEvent()
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled( self.camera_image_width,  self.camera_image_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        scene = QtWidgets.QGraphicsScene(self)
        self.setScene(scene)
        self.pixmap_item = QtWidgets.QGraphicsPixmapItem()
        scene.addItem(self.pixmap_item)

    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)

    def resizeEvent(self, event=None):
        self.fitInView(self.pixmap_item, QtCore.Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if a.imageIsZoomed:
            pass
        else:
            if self.pixmap_item is self.itemAt(event.pos()):
                sp = self.mapToScene(event.pos())
                lp = self.pixmap_item.mapFromScene(sp).toPoint()
                x = lp.x()
                y = lp.y()
                if event.button() == Qt.LeftButton:
                    a.left_Button_Moved = True
                    a.cords_list.append(x)
                    a.cords_list.append(y)
                elif event.button() == Qt.RightButton:
                    for i in range(a.apertureNumber):
                        x1 = a.cords_list[0 + (i * 4)]
                        x2 = a.cords_list[2 + (i * 4)]
                        y1 = a.cords_list[1 + (i * 4)]
                        y2 = a.cords_list[3 + (i * 4)]
                        if x2 < x1:
                            x1, x2 = x2, x1
                        if y2 < y1:
                            y1, y2 = y2, y1
                        if x1 <= x <= x2 and y1 <= y <= y2:
                            del a.cords_list[0 + (i * 4):4 + (i * 4)]
                            if a.currentAppertureNumber != 1:
                                a.currentAppertureNumber = a.currentAppertureNumber - 1
                            break


    def mouseMoveEvent(self, event):
        if a.imageIsZoomed:
            pass
        else:
            if self.pixmap_item is self.itemAt(event.pos()) and a.left_Button_Moved:
                a.mouse_Is_Moving = True
                sp = self.mapToScene(event.pos())
                lp = self.pixmap_item.mapFromScene(sp).toPoint()
                x = lp.x()
                y = lp.y()
                a.lastXtrackingPos = x
                a.lastYtrackingPos = y

    def mouseReleaseEvent(self, event):
        if a.imageIsZoomed:
            pass
        else:
            a.mouse_Is_Moving = False
            a.left_Button_Moved = False
            sp = self.mapToScene(event.pos())
            lp = self.pixmap_item.mapFromScene(sp).toPoint()
            x = lp.x()
            y = lp.y()
            if event.button() == Qt.LeftButton:
                if 0 <= x <= a.camera_image_width:
                    a.cords_list.append(x)
                elif x > a.camera_image_width:
                    x = a.camera_image_width
                    a.cords_list.append(x)
                elif x < 0:
                    x = 0
                    a.cords_list.append(x)
                if 0 <= y <= a.camera_image_width:
                    a.cords_list.append(y)
                elif y > a.camera_image_width:
                    y = a.camera_image_width
                    a.cords_list.append(y)
                elif y < 0:
                    y = 0
                    a.cords_list.append(y)
                a.mouseTrackingIsSafe = False
                a.apertureNumber = int(len(a.cords_list) / 4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    a = App()
    a.showMaximized()
    a.taskbar_button = QWinTaskbarButton()
    a.taskbar_button.setWindow(a.windowHandle())
    a.taskbar_button.setOverlayIcon(QtGui.QIcon('icon.ico'))
    sys.exit(app.exec_())
