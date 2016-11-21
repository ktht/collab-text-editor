import threading, common, os

class client_manager:

  def __init__(self, fn):
    self.fn = os.path.join(common.TMP_DIR_SERVER, fn.replace(common.DELIM_ID_FILE, os.path.sep))
    self.fd = None
    self.clients = []
    self.lock = threading.Lock()
    self.client_manager_thread_instance = client_manager_thread(self) # shall we daemonize it?

  @common.synchronized("lock") # lock this guy b/c we want to open one file and create one thread at only once
  def add_client(self, client_metadata):
    self.clients.append(client_metadata)

    if not os.path.exists(os.path.dirname(self.fn)):
      os.makedirs(os.path.dirname(self.fn))
    self.fd = open(self.fn, 'a+')
    # with a+ opening mode the stream is positioned at the end of the file; let's seek it to the beginning
    self.fd.seek(0)

    # screw it, let's send the file to the client
    # this function will be called in a separate thread dedicated to a client anyways
    if not client_metadata['create_file']:
      # send the whole contents of the file to the client
      for chunk in common.read_chunks(self.fd):
        client_metadata['socket'].sendall(chunk) # blocks!

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
    pass