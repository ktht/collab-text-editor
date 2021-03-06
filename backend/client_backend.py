import common, logging, socket, struct, threading, Queue

class client:

  queue_incoming = Queue.Queue()

  def __init__(self, addr, port, dirname, client_id = None):
    '''Initialize client instance (must be used on the client side!)
    :param addr:      string?, server address to connect to
    :param port:      int, server port to connect to
    :param dirname:   string, directory not sure why we use it
    :param client_id: int, client ID, may be left blank if the user don't know his/her ID
    '''
    self.addr_port = (addr, port)
    self.dir       = dirname
    self.id        = client_id
    self.fn        = None
    self.files     = []
    self.is_running = True

    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.debug('Created client socket, desciptor %d' % self.sock.fileno())

  def __enter__(self):
    '''Needed in with-as statements
    :return: This instance
    '''
    try:
      logging.debug("Connecting to server %s:%d" % self.addr_port)
      self.sock.connect(self.addr_port)
      logging.debug('Connected via %s:%d' % self.sock.getsockname())
      #self.sock.settimeout(common.TCP_CLIENT_TIMEOUT)                     # immediately blocks
      #logging.debug('Set the timeout to %ds' % common.TCP_CLIENT_TIMEOUT)
      #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,  common.TCP_CLIENT_KEEPALIVE)
      #self.sock.setsockopt(socket.SOL_TCP,    socket.TCP_KEEPIDLE,  common.TCP_CLIENT_KEEPIDLE)
      #self.sock.setsockopt(socket.SOL_TCP,    socket.TCP_KEEPINTVL, common.TCP_CLIENT_KEEPINTVL)
      #self.sock.setsockopt(socket.SOL_TCP,    socket.TCP_KEEPCNT,   common.TCP_CLIENT_KEEPCNT)
    except socket.error as err:
      logging.error('Encountered error while connecting to %s:%d; reason: %s' % (self.addr_port + (err,)))
    logging.debug('Client connected to %s:%d' % self.sock.getsockname())
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    '''Needed in with-as statements
    :return: None
    '''
    self.is_running = False
    self.sock.sendall(common.DELIM)
    common.close_socket(self.sock)


  def req_id(self):
    '''Request a new client ID from the server
    :return: int,  the new client ID if everything goes as expected
             None, if there was an error in the communication/[un]packing/whatever

     The function where it is called should check the returned value and act accordingly (preferably bail out).
    '''
    try:
      logging.debug('Requesting a new ID from the server')
      p_new_id = common.ctrl_struct.pack(*(common.CTRL_REQ_NEW_ID, 0))
      self.sock.sendall(p_new_id)
      p_new_id_resp = self.sock.recv(common.ctrl_struct.size)
      unp_new_id_resp = common.ctrl_struct.unpack(p_new_id_resp)
      new_id_resp_code, new_id = unp_new_id_resp
      if new_id_resp_code != common.CTRL_OK:
        raise ValueError('Server error')
      self.id = int(new_id)
    except socket.timeout as err:
      logging.debug('Socket timeout error: %s' % err)
      return None
    except socket.error as err:
      logging.debug('Socket error: %s' % err)
      return None
    except struct.error as err:
      logging.debug('Struct un/packing error: %s' % err)
      return None
    except KeyboardInterrupt as err:
      logging.debug('Caught SIGINT: %s' % err)
      return None
    except ValueError as err:
      logging.debug('Server error: %s' % err)
    except BaseException as err:
      logging.debug('Unknown error: %s' % err)
      return None
    return self.id

  def req_session(self):
    '''Reqiest a new session from the server
    :return: list of string, The list of files the server has stored for the user
    '''
    if self.id is None:
      logging.error("Yo, what's up! You have no ID and should request one "
                    "from the server before initiating the session (use: req_id())")
      return None
    try:
      logging.debug('Requesting a new session from the server')
      p_new_sess = common.ctrl_struct.pack(*(common.CTRL_REQ_INIT_SESS, self.id))
      self.sock.sendall(p_new_sess)
      p_new_sess_resp = common.recv(self.sock)
      if p_new_sess_resp is None:
        logging.error('Got an empty message?')
        return None
      new_sess_code, new_sess_files = p_new_sess_resp.split(common.DELIM_LONG)
      if int(new_sess_code) != common.CTRL_OK:
        logging.error('Server was not happy')
        return None
      self.files = new_sess_files.split(common.DELIM)
    except socket.timeout as err:
      logging.debug('Socket timeout error: %s' % err)
      return None
    except socket.error as err:
      logging.debug('Socket error: %s' % err)
      return None
    except struct.error as err:
      logging.debug('Struct un/packing error: %s' % err)
      return None
    except KeyboardInterrupt:
      logging.debug('Caught SIGINT')
      return None
    except BaseException as err:
      logging.debug('Unknown error: %s' % err)
      return None
    return self.files

  def req_file(self, fn, visibility = common.FILEMODE_PUBLIC):
    '''Returns file contents
    :param fn:          string, file name (id:file basename) to be opened
    :param visibility, int, sets the ownership if
                               a) the file is about to be created; and if
                               b) the value of `make_public' is set to either
                                    common.FILEMODE_PUBLIC or common.FILEMODE_PRIVATE
                             otherwise the visibility defaults to common.FILEMODE_DEFAULT on the server side
    :return: string, the contents of the file if everything succeeded
             None, if there was an error
    '''
    if self.id is None:
      logging.error("Yo, what's up! You have no ID and should request one "
                    "from the server before initiating the session (use: req_id())")
      return False
    self.fn = fn
    file_contents = ''
    try:
      logging.debug("Requesting to open file '%s' by server w/ opening mode '%d'" % (self.fn, visibility))
      req = common.DELIM.join([self.fn, str(visibility)])
      self.sock.sendall(req)
      p_new_file_resp = self.sock.recv(common.ctrl_struct.size)
      if not p_new_file_resp:
        logging.debug("Server was not happy")
        raise RuntimeError("Server was not happy b/c it didn't send us anything")
      new_file_code, _ = common.ctrl_struct.unpack(p_new_file_resp)
      if new_file_code == common.CTRL_OK_CREATE_FILE:
        logging.debug('Server had to create a new file, which is empty anyways')
      elif new_file_code == common.CTRL_OK_READ_FILE:
        logging.debug("Server has to serve the file for us; let's read it")
        # read from socket
        resp = common.recv(self.sock)
        if resp is None:
          logging.error("Server was not happy")
          raise RuntimeError("Server was not happy b/c it didn't send us anything")
        resp_code, file_contents = resp.split(common.DELIM)
        print("File contents: "+str(file_contents))
        if int(resp_code) == common.CTRL_OK:
          logging.debug('Received %d bytes of the file' % len(file_contents))
        else:
          logging.error('Server was not happy')
          raise RuntimeError('Server was not happy b/c it sent us a wrong control code')
      else:
        logging.error('Server was not happy')
        raise RuntimeError('Server was not happy b/c it sent us a wrong control code')

      # now boot up a new thread which listens to incoming edit control messages sent by the server
      # this thread should die only if
      #  a) self.is_running is set to False; or if
      #  b) the main thread exits (we daemonize the thread)
      receiving_thread = threading.Thread(
        target = self.recv_changes,
        name   = 'ReceiveFromServerThread'
      )
      receiving_thread.setDaemon(True)
      receiving_thread.start()

    except socket.timeout as err:
      logging.debug('Socket timeout error: %s' % err)
      return None
    except socket.error as err:
      logging.debug('Socket error: %s' % err)
      return None
    except struct.error as err:
      logging.debug('Struct un/packing error: %s' % err)
      return None
    except RuntimeError as err:
      logging.debug('Runtime error: %s' % err)
      return None
    except KeyboardInterrupt:
      logging.debug('Caught SIGINT')
      return None
    except BaseException as err:
      logging.debug('Unknown error: %s' % err)
      return None

    return file_contents

  def send_changes(self, line_no, action, payload = ''):
    '''Send changes in local file to the server
    :param line_no: int, Line number to be changed (line numbers start from 0)
    :param action:  int, Editing control code
                         (valid values: common.EDIT_REPLACE, common.EDIT_INSERT, common.EDIT_DELETE)
    :param payload: string, Value for the line (ignored if `action' is set to common.EDIT_DELETE)
    :return: True, if the request was successfully sent
             False, otherwise
    The file and client ID relevant to this request are defined in instance variables `self.id' and `self.fn'
    '''
    if self.id is None:
      logging.error("Yo, what's up! You have no ID and should request one "
                    "from the server before initiating the session (use: req_id())")
      return False
    if self.fn is None:
      logging.error("You haven't requested any files from the server. SMH")
      return False
    msg = common.marshall(line_no, action, payload, self.id)
    try:
      logging.debug("Send the changes made in file '%s' to the server" % self.fn)
      common.send(self.sock, msg)
    except socket.timeout as err:
      logging.debug('Socket timeout error: %s' % err)
      return False
    except socket.error as err:
      logging.debug('Socket error: %s' % err)
      return False
    except struct.error as err:
      logging.debug('Struct un/packing error: %s' % err)
      return False
    except RuntimeError as err:
      logging.debug('Runtime error: %s' % err)
      return False
    except KeyboardInterrupt:
      logging.debug('Caught SIGINT')
      return False
    except BaseException as err:
      logging.debug('Unknown error: %s' % err)
      return False
    return True

  def recv_changes(self):
    '''Receive messages from the server and put them into a queue
    :return: None (only if there was an interrupt or the variable `self.is_running' is set to False;
                   otherwise the receiving loop is always running regardless of caught exceptions)
    '''
    logging.debug('Starting to receive messages from the server')
    while self.is_running:
      try:
        msg = common.recv(self.sock)
        if msg is not None:
          unmarshalled_msg = common.unmarshall(msg)
          client.queue_incoming.put(unmarshalled_msg)
          logging.debug('Received a message from the server; pushed it into a queue')
        else:
          logging.debug("Server dropped?")
          break
      except socket.timeout as err:
        logging.debug('Socket timeout error: %s' % err)
        break
      except socket.error as err:
        logging.debug('Socket error: %s' % err)
        break
      except ValueError as err:
        logging.debug('Unmarshalling (?) error: %s' % err)
        break
      except RuntimeError as err:
        logging.debug('Runtime error: %s' % err)
        break
      except KeyboardInterrupt:
        logging.debug('Caught SIGINT')
        break
      except BaseException as err:
        logging.debug('Unknown error: %s' % err)
        break

    self.is_running = False