import threading, common, logging, file_manager, select, server_backend

class client_manager:

  KEY_SOCKET     = 'socket'      # socket object
  KEY_USERID     = 'user_id'     # int
  KEY_FILENAME   = 'filename'    # string
  KEY_CREATEFILE = 'create_file' # bool
  KEY_MAKEPUBLIC = 'make_public' # int

  # TODO: add support for common.FILEMODE_READONLY

  def __init__(self, fn):
    '''Initializes client manager class which basically handles incoming clients
       There must be one such manager per file (but there may be multiple clients which edit the file at the same time)
    :param fn: string, file name (id:file basename) to be opened
    '''
    self.fn = fn
    self.file_manager = file_manager.file_manager(fn)
    self.clients = {}
    self.outputs = {}
    self.lock = threading.Lock()
    self.client_manager_thread_instance = client_manager_thread(self) # shall we daemonize it?
    self.client_manager_thread_instance.setName('ClientManagerThread-%s' % fn)

  @common.synchronized("lock")
  def add_client(self, client_metadata):
    '''Adds a new client which takes part b/w the client-server communication
    :param client_metadata: dict, holds basic information about the client
    :return: None

     Lock this guy b/c we want to open one file and create one thread at only once
     @see client_manager_thread
    '''
    self.clients[client_metadata[client_manager.KEY_SOCKET]] = client_metadata

    # let's send the file to the client
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
    '''The thread handling communication about file changes b/w the server and the clients
    :param parent_manager: client_manager instance, The manager class holding information about incoming clients
    '''
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
        if msg and msg != common.DELIM:
          logging.debug("Received message from client #ID = '%d'" %
                        self.parent_manager.clients[r][client_manager.KEY_USERID])

          # let's parse the sent message and apply it on our file
          try:
            ret_edit = self.parent_manager.file_manager.edit(*common.unmarshall(msg))
            if not ret_edit:
              logging.debug("Encountered an error while editing the file")
              continue
          except ValueError as err:
            logging.debug("Encountered some kind of error in unmarshalling: %s" % err)
            if r not in exceptional:
              exceptional.append(r)
            continue

          # put into a queue
          for s in sockets:
            if s is not r:
              if s not in self.parent_manager.outputs:
                self.parent_manager.outputs[s] = []
              self.parent_manager.outputs[s].append(msg)
        else:
          logging.debug("Connection dropped with client #ID = '%d'?" %
                        self.parent_manager.clients[r][client_manager.KEY_USERID])
          if r in self.parent_manager.outputs:
            del self.parent_manager.outputs[r]
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

    logging.debug("No clients left, cleaning up")
    self.parent_manager.file_manager.close()
    del server_backend.server.managers[self.parent_manager.fn]