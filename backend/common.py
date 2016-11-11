# -*- coding: utf-8 -*-
import logging

SERVER_PORT_DEFAULT      = 7777
SERVER_INET_ADDR_DEFAULT = '127.0.0.1'      # localhost
BUF_SZ                   = 2**10            # 1kB

def close_socket(sock):
  import socket

  if not isinstance(sock, socket.socket):
    logging.debug('No socket to be closed')
    return

  try:
    sock.fileno()
  except socket.error:
    logging.debug('The socket is already closed')
    return

  sock.close()
  logging.debug('Closed the socket')