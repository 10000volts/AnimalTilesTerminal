import socket

from myio import IO
from game import Game
from utils.color import color, color_print, EColor

if __name__ == '__main__':
  port = 5555

  color_print("欢迎光临花鸟瓷砖~")
  color_print("作为客户端吗？(y/n)")
  client = (input() == 'y')
  color_print("输入目标ip")
  ip = input()
  # color_print("输入目标port")
  # port = input()
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  if client:
    try:
      s.connect((ip, port))
    except Exception as ex:
      color_print(ex, EColor.ERROR)
      color_print("连接服务端失败。退出。", EColor.ERROR)
      exit()

    io = IO(s)
    color_print("已加入比赛！", EColor.EMPHASIS)

    g = Game(True, io)
    g.start()

    s.close()
  else:
    try:
      s.bind((ip, port))
    except Exception as ex:
      color_print(ex, EColor.ERROR)
      color_print("服务端创建失败。退出。", EColor.ERROR)
      exit()
    s.listen(5)
    color_print("等待对方加入比赛...", EColor.EMPHASIS)
    conn, addr = s.accept()

    color_print("{}加入了比赛！".format(color(addr, EColor.EMPHASIS)))
    io = IO(s)
    g = Game(False, io)
    g.start()

    conn.close()
    s.close()
