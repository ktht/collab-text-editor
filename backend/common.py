# -*- coding: utf-8 -*-
import logging, struct, os, functools

SERVER_PORT_DEFAULT      = 7777            # default port
SERVER_INET_ADDR_DEFAULT = '127.0.0.1'     # localhost
BUF_SZ                   = 2**10           # 1kB
MAX_PDU_SZ               = 10 * (2**10)**2 # 10MB

ctrl_struct = struct.Struct('I Q') # unisnged int + unsigned long long (9 bytes in total)
CTRL_OK            = int(0x01 << 0)
CTRL_REQ_NEW_ID    = int(0x01 << 1)
CTRL_REQ_INIT_SESS = int(0x01 << 2)
CTRL_REQ_FILE      = int(0x01 << 3)

TMP_DIR = os.path.join(os.path.expanduser('~'), '.tmp_collab')

DELIM         = '\0'
DELIM_ID_FILE = ':'

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

def read_chunks(fo, chunk_size = MAX_PDU_SZ):
  while True:
    data = fo.read(chunk_size)
    if not data:
      break
    yield data

def recv(sock, buf_sz = BUF_SZ):
  msg = ''
  while True:
    resp = sock.recv(buf_sz)
    if resp:
      msg += resp
    else:
      break
  return msg

def synchronized(lock_name):
  def wrapper(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
      logging.debug("Acquiring lock: %s" % lock_name)
      lock = getattr(self, lock_name)
      with lock:
        result = func(self, *args, **kwargs)
      logging.debug("Released lock: %s" % lock_name)
      return result
    return decorator
  return wrapper