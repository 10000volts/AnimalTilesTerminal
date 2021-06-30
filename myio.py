class IO:
  def __init__(self, s) -> None:
    self.socket = s

  def send(self, message):
    self.socket.send((message + '|').encode())

  def recv(self):
    recv =  self.socket.recv(1024).decode().split('|')
    while len(recv) == 0:
      recv =  self.socket.recv(1024).decode().split('|')
    return recv