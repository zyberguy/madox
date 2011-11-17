"""
MWRover - Mecanum Wheel Rover Base
http://www.madox.net/
"""

import serial
import struct

import cgi
import BaseHTTPServer
import SocketServer
import threading

PORT="/dev/ttyACM0"
BAUDRATE = 9600
BYTESIZE = 8
PARITY   = serial.PARITY_NONE
STOPBITS = 1
XONXOFF  = False
RTSCTS   = False

HTTP_HOST  = ""
HTTP_PORT  = 8080

class MaestroServo():
  def __init__(self):
    self.ser            = serial.Serial()
    self.ser.port       = PORT
    self.ser.baudrate   = BAUDRATE
    self.ser.bytesize   = BYTESIZE
    self.ser.parity     = PARITY
    self.ser.stopbits   = STOPBITS
    self.ser.xonxoff    = XONXOFF
    self.ser.rtscts     = RTSCTS
        
    self.Frame          = []
    self.FrameBCC       = 0x00
    self.ser.open()
    self.ser.flushInput()
    self.ser.flushOutput()
            
    self.shutdown = False
    
  def setTarget(self, id, target_us):
    target_qus = int(target_us * 4)
    frame=[]
    frame.append(0x84)
    frame.append(id)
    frame.append(target_qus & 0b0000000001111111)
    frame.append((target_qus & 0b0011111110000000)>>7)
    self.sendFrame(frame)

  def goHome(self):
    frame = 0xA2
    self.sendFrame(frame)

  def sendFrame(self, frame):
    framestr = ''
    for char in frame:
      #print "%0x" % char
      framestr += chr(char)
    self.ser.write(framestr)
          
class MWHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  def __init__(self, server_address, RequestHandlerClass, MaestroClass):
    SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
    self.MServo = MaestroClass()    
    
class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """
  HTTP Request Handler
  """
  def do_GET(self):
    #Get /MWRover.* case or /www/*
    if self.path[:8] == "/MWRover" or self.path[:5] == "/www/":
      try:
        f = open(self.path[1:], "r")
        Response = f.read()
        self.send_response(200)
        self.send_header("Content-Length", str(len(Response)))
        self.end_headers()
        self.wfile.write(Response)
        f.close()
      except:
        self.send_error(404, "Banana Not Found.")
        self.end_headers()
    else:
      self.send_error(404, "Banana Not Found.")
      self.end_headers()
  def do_POST(self):
    if self.path == "/command/":
      form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={ 'REQUEST_METHOD':'POST',
                          'CONTENT_TYPE':self.headers['Content-Type']
                        }    )
      
      self.send_response(200)
      self.end_headers()
      
      for field in form.keys():
        item = form[field]
        if item.filename:
          #Someone posted me a file and I don\'t know what I should do with it
          pass
        else:
          #Normal form value
          field, item.value
          print "Got command", field, ":", item.value
          self.server.MServo.setTarget(int(field), float(item.value))
    else:
      self.send_error(405)
      self.end_headers()
      
  def log_message(self, format, *args):
    #Disable standard log messages
    pass
  do_HEAD = do_GET

if __name__ == '__main__':
  HTTPServer = MWHTTPServer((HTTP_HOST,HTTP_PORT),HTTPHandler,MaestroServo)
  print "Started MWRover Control"
  HTTPServer_thread = threading.Thread(target = HTTPServer.serve_forever())
  HTTPServer_thread.setDaemon(true)
  HTTPServer_thread.start()
  
  try:
    while True:
      pass
  except KeyboardInterrupt:
    HTTPServer.shutdown()
