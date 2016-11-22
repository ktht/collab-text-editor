# -*- coding: utf-8 -*-
import logging, struct, os, functools

SERVER_PORT_DEFAULT      = 7777            # default port
SERVER_INET_ADDR_DEFAULT = '127.0.0.1'     # localhost
BUF_SZ                   = 2**10           # 1kB
MAX_PDU_SZ               = 10 * (2**10)**2 # 10MB
TCP_CLIENT_TIMEOUT       = 10               # 10 seconds
TCP_CLIENT_KEEPALIVE     = 1                # 1 second
TCP_CLIENT_KEEPIDLE      = 1                # 1 second
TCP_CLIENT_KEEPINTVL     = 1                # 1 second
TCP_CLIENT_KEEPCNT       = 5                # 5 seconds

ctrl_struct = struct.Struct('I Q') # unisnged int + unsigned long long (9 bytes in total)
CTRL_OK             = int(0x01 << 0)
CTRL_OK_CREATE_FILE = int(0x01 << 1)
CTRL_OK_READ_FILE   = int(0x01 << 2)
CTRL_REQ_NEW_ID     = int(0x01 << 3)
CTRL_REQ_INIT_SESS  = int(0x01 << 4)
CTRL_REQ_FILE       = int(0x01 << 5)

TMP_DIR = os.path.join(os.path.expanduser('~'), '.tmp_collab')
TMP_DIR_SERVER = os.path.join(TMP_DIR, 'server')
TMP_DIR_CLIENT = os.path.join(TMP_DIR, 'client')
TMP_DIR_TEST   = os.path.join(TMP_DIR, 'test')

DELIM         = '\0'
DELIM_LONG    = '\0' * 3
DELIM_ID_FILE = ':'

EDIT_DELETE  = int(0x01 << 0)
EDIT_REPLACE = int(0x01 << 1)
EDIT_INSERT  = int(0x01 << 2)

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

def marshall(line_no, action, payload): # payload must not contain any newline characters
  # client_id
  assert(type(line_no) == int and type(action) == int and type(payload) == str)
  assert(line_no >= 0)
  assert(action in (EDIT_DELETE, EDIT_REPLACE, EDIT_INSERT))
  msg = DELIM.join([str(line_no), str(action), payload])
  return msg

def unmarshall(msg):
  assert(type(msg) == str)
  split = msg.split(DELIM)
  assert(len(split) == 3)
  line_no, action, payload = int(split[0]), int(split[1]), split[2]

  assert (line_no >= 0)
  assert(action in (EDIT_DELETE, EDIT_REPLACE, EDIT_INSERT))
  return line_no, action, payload

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