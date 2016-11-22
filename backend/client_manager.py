import threading, common, logging, file_manager, atexit, select

class client_manager:

  def __init__(self, fn):
    self.file_manager = file_manager.file_manager(fn)
    self.clients = {}
    self.outputs = {}
    self.lock = threading.Lock()
    self.client_manager_thread_instance = client_manager_thread(self) # shall we daemonize it?
    atexit.register(self.file_manager.close) # shameless hack :)

  @common.synchronized("lock") # lock this guy b/c we want to open one file and create one thread at only once
  def add_client(self, client_metadata):
    self.clients[client_metadata['socket']] = client_metadata

    # screw it, let's send the file to the client
    # this function will be called in a separate thread dedicated to a client anyways
    if not client_metadata['create_file']:
      logging.debug('Reading an existing file')
      # send the whole contents of the file to the client
      file_contents = self.file_manager.str()
      msg = str(common.CTRL_OK) + common.DELIM + file_contents
      client_metadata['socket'].sendall(msg)

    if not self.client_manager_thread_instance.isAlive():
      # this means that the thread handling the communication b/w the server and clients has not even been started yet
      # let's start it now
      self.client_manager_thread_instance.start()

class client_manager_thread(threading.Thread):

  def __init__(self, parent_manager):
    threading.Thread.__init__(self)
    self.parent_manager = parent_manager

  def run(self):
    # here be the select() loop
    # check for self.parent.clients in the while loop

    #TODO: timeout in select.select() ????????????????

    while len(self.parent_manager.clients) > 0:
      sockets = self.parent_manager.clients.keys()
      outputs = self.parent_manager.outputs.keys()
      readable, writable, exceptional = select.select(sockets, outputs, sockets)

      for r in readable:
        msg = r.recv(common.BUF_SZ)
        if msg:
          logging.debug("You've got mail (it's an AOL joke)")

          # let's parse the sent message and apply it on our file
          self.parent_manager.file_manager.edit(*common.unmarshall(msg))

          # put into a queue
          for s in sockets:
            if s is not r:
              if r not in self.parent_manager.outputs:
                self.parent_manager.outputs = []
              self.parent_manager.outputs[s].append(msg)
        else:
          logging.debug("Connection dropped?")
          if r in self.parent_manager.outputs:
            self.parent_manager.outputs.remove(r)
          del self.parent_manager.clients[r]
          r.close()
      for w in writable:
        if w in self.parent_manager.outputs:
          while len(self.parent_manager.outputs[w]) > 0:
            logging.debug('Broadcasting the changes to other guys')
            w.sendall(self.parent_manager.outputs[w].pop(0))
      for e in exceptional:
        logging.debug('Client dropped?')
        if e in self.parent_manager.outputs:
          del self.parent_manager.outputs[e]
        if e in self.parent_manager.clients:
          del self.parent_manager.clients[e]