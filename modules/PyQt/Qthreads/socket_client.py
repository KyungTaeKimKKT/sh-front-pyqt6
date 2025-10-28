from PyQt6.QtCore import *
import json, numpy, base64, time, datetime
import cv2
import socket
import sounddevice
import pickle

import modules.user.utils as utils


class Socket_client(QThread):
    """ Socket Server... data가 들어오면 signal_received emit"""
    signal_received = pyqtSignal(object) 

    def __init__(self, parent, ip, port, fileInfo:dict):
        super().__init__(parent)
        self.TCP_IP = ip
        self.TCP_PORT = port
        self.fileInfo = fileInfo
        self.fileSize = fileInfo.get('fileSize')
        self.fileName = fileInfo.get('fileName')
        self.header_len = 1024
        self.sock = None
        self.conn = None
        self.is_Run = True

        self.socketOpen()

        self.FirstHEADER_LEN = 16
        self.socketErrCnt = 0



    def run(self):
        while self.is_Run and self.sock is not None:            
            try:                
                # t0 = time.time()
                # header_len = str(self.recvall(self.conn, self.FirstHEADER_LEN).decode('utf-8')).strip()
                # header = self.recvall(self.conn, int(header_len))
                # # print ( '받은:', header )
                # header = header.decode('utf-8')
                # # print ( 'decode 후:', header )
                # headerDict = json.loads(header)
                # headerDict['connected_to'] = self.conn.getpeername()[0]
                streamingData = self.recvall(self.sock, self.fileSize )     
           
                if streamingData : 
                    self.signal_received.emit(streamingData)
                    self.close()
                # self.close()
                

            except Exception as e:
                utils.pprint(f'{self.TCP_PORT} socket error:{e} ')
                self.socketErrCnt +=1
                if self.socketErrCnt > 5 :
                    utils.pprint(f'socket close by {self.socketErrCnt} errors')
                    self.close()

                # continue
                # self.socketClose()
                # cv2.destroyAllWindows()
                # self.socketOpen()

    def stop(self):
        self.is_Run = False
        
    def close(self):
        self.stop()
        self.socketClose()

    def restart(self):
        self.is_Run = True

    def socketClose(self):
        # OSError: [Errno 9] 파일 디스크립터가 잘못됨
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


    def socketOpen(self):

        try:
            if self.sock is None:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect( (self.TCP_IP, self.TCP_PORT) )
                sendData = json.dumps( self.fileInfo, ensure_ascii=False)
                self.sock.sendall( sendData.encode('utf-8').ljust(self.header_len))
            # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:

    
    def tts(self, msg):
        strType = 'tts'
   
        HEADER = {
            'type':strType,
            'format' : 'text', 
            'stime' : datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f'),
            'tts': msg,
        }

        json_str = json.dumps(HEADER, ensure_ascii=False).encode('utf-8')

        self.conn.send (str(len(json_str)).encode('utf-8').ljust(16))
        self.conn.sendall( json_str )

    def ftp_ready(self):
        pass
        
    def ftp(self, fName, file):        
        if self.conn is None:  self.conn, self.addr = self.sock.accept()


        stime = time.time()
        strType = 'ftp'
        streamData = file.read()
        if not streamData : 
            utils.pprint('ftp streamData is Empty')
            return
        # streamData = str(data).encode()

        HEADER = {
            'type':strType,
            'fName' : fName, 
            'stime' : datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f'),
            'fileLength': len(streamData) ,
        }
        json_str = json.dumps(HEADER, ensure_ascii=False).encode('utf-8')
        self.conn.send (str(len(json_str)).encode('utf-8').ljust(16))
        self.conn.sendall( json_str )
        self.conn.sendall( streamData )

    # def receiveImages(self):

    #     try:
    #         while True:
    #             length = self.recvall(self.conn, 64)
    #             length1 = length.decode('utf-8')
    #             stringData = self.recvall(self.conn, int(length1))
    #             stime = self.recvall(self.conn, 64)

    #             now = time.localtime()

    #             # print('receive time: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'))
    #             data = numpy.frombuffer(base64.b64decode(stringData), numpy.uint8)
    #             decimg = cv2.imdecode(data, 1)
    #             self.timeout.emit(decimg)
    #             # cv2.imshow("image", decimg)
    #             # cv2.waitKey(1)
    #     except Exception as e:

    #         self.socketClose()
    #         cv2.destroyAllWindows()
    #         self.socketOpen()
    #         self.receiveThread = threading.Thread(target=self.receiveImages)
    #         self.receiveThread.start()
        
    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf

