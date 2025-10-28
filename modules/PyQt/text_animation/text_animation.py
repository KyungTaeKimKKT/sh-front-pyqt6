import sys

from PyQt6.QtCore import QEvent, QTimer, pyqtSlot,QRectF, pyqtSignal
from PyQt6.QtGui import QTextDocument, QPainter, QFontMetrics,QFont,QColor,QAbstractTextDocumentLayout,QPalette
from PyQt6.QtWidgets import QLabel, QApplication
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Document(QTextDocument):
    def __init__(self, parent=None):
        super().__init__(parent)

    def drawContents(self, p, rect=QRectF()):
        p.save()
        ctx=QAbstractTextDocumentLayout.PaintContext ()
        ctx.palette.setColor(QPalette.ColorRole.Text, p.pen().color())
        if (rect.isValid()) :
            p.setClipRect(rect)
            ctx.clip = rect
        self.documentLayout().draw(p, ctx)
        p.restore()

class Marquee(QLabel):
    signal_finished = pyqtSignal()

    paused = False
    speed = 60
    x=0
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value , self.mode = '', ''
        self.document = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.translate)
    
    # def resizeEvent(self, a0):
    #     self.setText( self.value, self.mode )
    #     return super().resizeEvent(a0)

    def setText(self, value,mode ="R+L"):
        if self.timer.isActive() :
            self.timer.stop()

        self.value = value
        self.mode = mode

        maxWidth = self.width()

        f=self.font()
        self.fm=QFontMetrics(f)
        if self.document is  None:
            self.document = Document(self)
            self.document.setUseDesignMetrics(True)
        self.document.setDefaultFont(f)
        self.document.setDocumentMargin(0)
        


        fm_width = self.fm.boundingRect(value).width()

        self.nl = int(maxWidth /self.fm.horizontalAdvance(" "))
        val=' '*self.nl +value+' '*self.nl 
        self.document.setTextWidth(self.fm.boundingRect(val).width() +22 )
        self.document.clear()
        self.document.setPlainText(val)
        self.setMode(mode)
        self.timer.start(int((1 / 60) * 1000) )

        # if fm_width  > maxWidth :
        #     self.nl = int(maxWidth /self.fm.horizontalAdvance(" "))
        #     val=' '*self.nl +value+' '*self.nl 
        #     self.document.setTextWidth(self.fm.boundingRect(val).width() +22 )
        #     self.document.clear()
        #     self.document.setPlainText(val)
        #     self.setMode(mode)
        #     self.timer.start(int((1 / 60) * 1000) )
        # else:
        #     self.x=(maxWidth /2)-(fm_width/2)
        #     self.document.clear()
        #     self.document.setPlainText(value)
        #     self.repaint()
    
    def setMode(self,val):
        if val=="RL":
            self.x = 0
        elif val=="LR"  :  
            self.x =-(self.document.textWidth()-self.fm.boundingRect(" "*self.nl).width()-10)
        else:
            self.x =-(self.document.textWidth()-self.fm.boundingRect(" "*self.nl).width()-10)
            self.fstr=True    
        self.mode=val 

    @pyqtSlot()
    def translate(self):
        if not self.paused:
            if self.mode=="RL":
                if self.width() - self.x < self.document.textWidth():
                    self.x -= 1   
                else:
                    self.x=0
                    self.signal_finished.emit()

            elif  self.mode=="LR"  :
                if self.x<=0:
                    self.x+= 1 
                else:   
                    self.x =-(self.document.textWidth()-self.fm.boundingRect(" "*self.nl).width()-10)
            else:
                if self.fstr:
                    if self.x<=0:
                        self.x+= 1 
                    else:   
                        self.x =0
                        self.fstr=False
                else:
                    if self.width() - self.x < self.document.textWidth():
                        self.x -= 1   
                    else:
                        self.x=-(self.document.textWidth()-self.fm.boundingRect(" "*self.nl).width()-10)
                        self.fstr=True 

        self.repaint()

    # def event(self, event):
    #     if event.type() == QEvent.Enter:
    #         self.paused = True
    #     elif event.type() == QEvent.Leave:
    #         self.paused = False
    #     return super().event(event)
    def getColor(self)->QColor:
        if self.styleSheet()=='':
            return QColor("grey")
        else:
            style =self.styleSheet().split(";")
            color= "".join([s.split(":")[1] for s in style if s.startswith("color")])    
            return QColor(color)
        
    def paintEvent(self, event):
        if self.document:
            p = QPainter(self)
            self.getColor()
            p.setPen(self.getColor())
            p.translate(self.x, 0)
            self.document.drawContents(p)
        return super().paintEvent(event)
    

if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = Marquee()
    w.setFixedSize(250, 60)
    w.setStyleSheet("background-color:black;color:yellow")
    f=QFont()
    f.setPointSize(20)
    f.setBold(True)
    f.setItalic(True)
    f.setFamily("Courier")
    w.setFont(f)
    w.setText("consectggftr_conversion_we want",mode="L+R") # or "RL" or "LR"

    w.show()

    app.exec()