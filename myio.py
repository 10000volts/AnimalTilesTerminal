class IO:
  def __init__(self, s) -> None:
    self.socket = s

  def send(self, message):
    self.socket.send((message + '|').encode())

  def recv(self):
    d = self.socket.recv(2048).decode()
    while d[-1] != '|':
      d += self.socket.recv(2048).decode()
    return d.split('|')[0]