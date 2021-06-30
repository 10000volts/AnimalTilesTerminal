class IO:
  def __init__(self, s) -> None:
    self.socket = s
    self._temp = list()

  def send(self, message):
    self.socket.send((message + '|').encode())

  def recv(self):
    if len(self._temp):
      return self._temp.pop(0)
    d = self.socket.recv(2048).decode()
    while d == '' or d[-1] != '|':
      d += self.socket.recv(2048).decode()
    self._temp.extend(d.split('|')[:-1])
    return self._temp.pop(0)