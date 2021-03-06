# -*- coding: utf-8 -*-
import logging, struct, os, functools, socket

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

DELIM           = '\0'
DELIM_LONG      = DELIM * 3
DELIM_LONG_LONG = DELIM * 5
DELIM_ID_FILE   = ':'
MSG_TERMINATOR  = DELIM_LONG_LONG

EDIT_DELETE  = int(0x01 << 0)
EDIT_REPLACE = int(0x01 << 1)
EDIT_INSERT  = int(0x01 << 2)

EDIT_STRINGS = {
  EDIT_DELETE  : 'DELETE',
  EDIT_REPLACE : 'REPLACE',
  EDIT_INSERT  : 'INSERT',
}

FILEMODE_PUBLIC   = int(0x01 << 0)
FILEMODE_PRIVATE  = int(0x01 << 1)
FILEMODE_DEFAULT  = int(0x01 << 2)

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

def recv(sock, buf_sz = BUF_SZ):
  msg = ''
  try:
    while not msg.endswith(MSG_TERMINATOR):
      resp = sock.recv(buf_sz)
      if resp:
        msg += resp
      else:
        break
  except socket.timeout as err:
    logging.debug("Socket timeout error: %s" % err)
    return None
  except socket.error as err:
    logging.debug("Socket error: %s" % err)
    return None
  return msg[:-len(MSG_TERMINATOR)]

def send(sock, msg):
  sock.sendall(msg + MSG_TERMINATOR)

def marshall(line_no, action, payload, id):
  '''Marshalls the edit command into string meant for sendng across TCP pipe
  :param line_no: int, Line number to be edited
  :param action:  int, Edit control code
                       (valid values: EDIT_DELETE, EDIT_REPLACE, EDIT_INSERT)
  :param payload: string, New line (use an empty string if the edit control code is EDIT_DELETE)
  :return: string, The marshalled message
  '''
  if not (type(line_no) == int and type(action) == int and type(payload) == str and type(id) == int):
    raise ValueError("Invalid input types")
  if not (line_no >= 0):
    raise ValueError("Invalid row number (must be a positive integer)")
  if not (action in (EDIT_DELETE, EDIT_REPLACE, EDIT_INSERT)):
    raise ValueError("Invalid edit control code")
  msg = DELIM.join([str(line_no), str(action), payload, str(id)])
  return msg

def unmarshall(msg):
  '''Unmarshalls a given string which is expected to have the xzme format as in marshall() function
  :param msg: string, The message to be unmarshalled
  :return: (int, int, string), The line number to be edited,
                               the edit control code (valid values: EDIT_DELETE, EDIT_REPLACE, EDIT_INSERT)
                               new line
  '''
  if not (type(msg) == str):
    raise ValueError("Wrong type to be unmarshalled (must be a string)")
  split = msg.split(DELIM)
  if not (len(split) == 4):
    raise ValueError("Invalid number of elements marshalled into the message (must be 4)")
  line_no, action, payload, id = int(split[0]), int(split[1]), split[2], split[3]

  if not (line_no >= 0):
    raise ValueError("Invalid row number (must be a positive integer)")
  if not (action in (EDIT_DELETE, EDIT_REPLACE, EDIT_INSERT)):
    raise ValueError("Invalid edit control code")
  return line_no, action, payload, id

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