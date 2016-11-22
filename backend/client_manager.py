import threading, common, logging, file_manager, atexit, select

class client_manager:

  KEY_SOCKET     = 'socket'
  KEY_USERID     = 'user_id'
  KEY_FILENAME   = 'filename'
  KEY_CREATEFILE = 'create_file'

  def __init__(self, fn):
    self.file_manager = file_manager.file_manager(fn)
    self.clients = {}
    self.outputs = {}
    self.lock = threading.Lock()
    self.client_manager_thread_instance = client_manager_thread(self) # shall we daemonize it?
    atexit.register(self.file_manager.close) # shameless hack :)

  @common.synchronized("lock") # lock this guy b/c we want to open one file and create one thread at only once
  def add_client(self, client_metadata):
    self.clients[client_metadata[client_manager.KEY_SOCKET]] = client_metadata

    # screw it, let's send the file to the client
    # this function will be called in a separate thread dedicated to a client anyways
    if not client_metadata[client_manager.KEY_CREATEFILE]:
      logging.debug('Reading an existing file')
      # send the whole contents of the file to the client
      file_contents = self.file_manager.str()
      msg = str(common.CTRL_OK) + common.DELIM + file_contents
      client_metadata[client_manager.KEY_SOCKET].sendall(msg)

    if not self.client_manager_thread_instance.isAlive():
      # this means that the thread handling the communication b/w the server and clients has not even been started yet
      # let's start it now
      self.client_manager_thread_instance.start()

class client_manager_thread(threading.Thread):

  def __init__(self, parent_manager):
    threading.Thread.__init__(self)
    self.parent_manager = parent_manager

  def run(self):
    '''Sender/receiver part in the server, one per file
    :return: None
    '''
    while len(self.parent_manager.clients) > 0:
      sockets = self.parent_manager.clients.keys()
      outputs = self.parent_manager.outputs.keys()
      readable, writable, exceptional = select.select(sockets, outputs, sockets)

      for r in readable:
        msg = r.recv(common.BUF_SZ)
        if msg:
          logging.debug("Received message from client #ID = '%d'" %
                        self.parent_manager.clients[r][client_manager.KEY_USERID])

          # let's parse the sent message and apply it on our file
          self.parent_manager.file_manager.edit(*common.unmarshall(msg))

          # put into a queue
          for s in sockets:
            if s is not r:
              if r not in self.parent_manager.outputs:
                self.parent_manager.outputs = []
              self.parent_manager.outputs[s].append(msg)
        else:
          logging.debug("Connection dropped with client #ID = '%d'?" %
                        self.parent_manager.clients[r][client_manager.KEY_USERID])
          if r in self.parent_manager.outputs:
            self.parent_manager.outputs.remove(r)
          del self.parent_manager.clients[r]
          r.close()
      for w in writable:
        if w in self.parent_manager.outputs:
          while len(self.parent_manager.outputs[w]) > 0:
            logging.debug("Sending the changes to client #ID = '%d'" %
                          self.parent_manager.clients[w][client_manager.KEY_USERID])
            w.sendall(self.parent_manager.outputs[w].pop(0))
      for e in exceptional:
        logging.debug("Client #ID = '%d' dropped connection" %
                      self.parent_manager.clients[e][client_manager.KEY_USERID])
        if e in self.parent_manager.outputs:
          del self.parent_manager.outputs[e]
        if e in self.parent_manager.clients:
          del self.parent_manager.clients[e]
