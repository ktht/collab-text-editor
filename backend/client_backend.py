import common, logging, socket, struct

#TODO: COMMENT ME

class client:

  def __init__(self, addr, port, dirname, client_id = None):
    self.addr_port = (addr, port)
    self.dir       = dirname
    self.id        = client_id

    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.debug('Created client socket, desciptor %d' % self.sock.fileno())

  def __enter__(self):
    try:
      self.sock.connect(self.addr_port)
      logging.debug('Connecting via %s:%d' % self.sock.getsockname())
      self.sock.settimeout(common.TCP_CLIENT_TIMEOUT)                     # immediately blocks
      logging.debug('Set the timeout to %ds' % common.TCP_CLIENT_TIMEOUT)
      self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,  common.TCP_CLIENT_KEEPALIVE)
      self.sock.setsockopt(socket.SOL_TCP,    socket.TCP_KEEPIDLE,  common.TCP_CLIENT_KEEPIDLE)
      self.sock.setsockopt(socket.SOL_TCP,    socket.TCP_KEEPINTVL, common.TCP_CLIENT_KEEPINTVL)
      self.sock.setsockopt(socket.SOL_TCP,    socket.TCP_KEEPCNT,   common.TCP_CLIENT_KEEPCNT)
    except socket.error as err:
      logging.error('Encountered error while connecting to %s:%d; reason: %s' % (self.addr_port + (err,)))
    logging.debug('Client connected to %s:%d' % self.sock.getsockname())
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    common.close_socket(self.sock)

  def req_id(self):
    try:
      p_new_id = common.ctrl_struct.pack(*(common.CTRL_REQ_NEW_ID, 0))
      self.sock.sendall(p_new_id)
      p_new_id_resp = self.sock.recv(common.ctrl_struct.size)
      unp_new_id_resp = common.ctrl_struct.unpack(p_new_id_resp)
      new_id_resp_code, new_id = unp_new_id_resp
      if new_id_resp_code != common.CTRL_OK:
        raise ValueError('Server error')
      self.id = new_id
    except socket.timeout as err:
      logging.debug('Socket timeout error: %s' % err)
      return False
    except socket.error as err:
      logging.debug('Socket error: %s' % err)
      return False
    except struct.error as err:
      logging.debug('Struct un/packing error: %s' % err)
      return False
    except KeyboardInterrupt as err:
      logging.debug('Caught SIGINT: %s' % err)
      return False
    except ValueError as err:
      logging.debug('Server error: %s' % err)
    except BaseException as err:
      logging.debug('Unknown error: %s' % err)
      return False
    return True

  def req_session(self):
    try:
      pass
    except socket.timeout:
      logging.debug('Socket timeout error')
      return False
    except socket.error:
      logging.debug('Socket error')
      return False
    except struct.error:
      logging.debug('Struct un/packing error')
      return False
    except KeyboardInterrupt:
      logging.debug('Caught SIGINT')
      return False
    except BaseException:
      logging.debug('Unknown error')
      return False
    return True

  def req_file(self):
    try:
      pass
    except socket.timeout:
      logging.debug('Socket timeout error')
      return False
    except socket.error:
      logging.debug('Socket error')
      return False
    except struct.error:
      logging.debug('Struct un/packing error')
      return False
    except KeyboardInterrupt:
      logging.debug('Caught SIGINT')
      return False
    except BaseException:
      logging.debug('Unknown error')
      return False
    return True

  def init_session(self):
    pass