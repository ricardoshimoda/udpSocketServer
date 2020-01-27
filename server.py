import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0
xStep = 1.5

clients = {}


# this is the receiving message loop 
def connectionLoop(sock):
   global xStep
   global connected
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         # received a heartbeat
         if 'heartbeat' in data:
            #updates heartbeat data to make sure client is still alive
            clients[addr]['lastBeat'] = datetime.now()
         if 'cube_position' in data:
            print(data)
            positionMessage = data[2:-1]
            print(positionMessage)
            positionData = json.JSONDecoder().decode(positionMessage)
            clients[addr]['position'] = positionData['position']
      else:
         # new client - receives a connect
         if 'connect' in data:
            # This deal with new connections
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
            # Calculate the position of the newly acquired member
            finalCount = connected + 1
            xCoord = (finalCount//2) * xStep
            #print(xCoord)
            if (int(finalCount) % 2 == 1):
               xCoord = -1 * xCoord
            clients[addr]['position'] = {"x": xCoord,"y":0.0, "z":0.0}
            # Sends information of the new connected client to everyone - but the newly connected client
            message = {"cmd": 0,"players":[{"id":str(addr), "color": clients[addr]['color'], "position": clients[addr]['position']}]}
            m = json.dumps(message)
            for c in clients:
               if c != addr :
                  #print('NEW messsage: ')
                  #print(m)
                  #print('**************************************')
                  sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
            
            #print("Now going to the other message")
            # Sends information of all connected clients to the newly connected client
            Others = {"cmd": 2, "players": []}
            for c in clients:
               player = {}
               player['id'] = str(c)
               player['color'] = clients[c]['color']
               player['position'] = clients[c]['position']
               Others['players'].append(player)
            oth=json.dumps(Others)
            #print('OTHERS messsage: ')
            #print(oth)
            #print('**************************************')
            sock.sendto(bytes(oth,'utf8'), (addr[0], addr[1]))
            connected += 1

# Every second verifies if clients are still active or not based on their heartbeat
def cleanClients(sock):
   while True:
      needToSend = False
      deleteMessage = {"cmd": 3,"players":[]}
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            needToSend = True
            print('Dropped Client: ', c)
            player = {}
            player['id'] = str(c)
            player['color'] = clients[c]['color']
            deleteMessage['players'].append(player)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()

      if needToSend :
         print('Sending DELETE message')
         dm = json.dumps(deleteMessage)
         for f in clients:
            sock.sendto(bytes(dm,'utf8'), (f[0],f[1]))

      time.sleep(1)

# Every second sends message about whoelse is still connected to the server
def gameLoop(sock):
   while True:
      # This sends the UPDATE (1) message to the client
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      #print (clients)
      for c in clients:
         player = {}
         #Change color
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}         
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
   
