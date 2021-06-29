import random

def shuffle(l: list):
  for i in range(0, len(l)):
    j = random.randint(0, len(l) - 1)
    temp = l[i]
    l[i] = l[j]
    l[j] = temp