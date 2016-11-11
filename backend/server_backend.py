import common, logging, socket, shutil, os, threading, struct, tempfile

metainfo = {
  'description' : '{name} {version} %s (%s)'.format(
                  name = 'Collab text editor server', version='0.0.1', built='11/11/16'
  )
}

class server:
  tcp_client_queue = 10

  def __init__(self, addr, port, directory):
    logging.debug('Starting %s' % metainfo['description'])

    self.addr_port = (addr, port)
    self.directory = os.path.abspath(directory)

    self.socket   = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

  def __enter__(self):
    if not os.path.exists(self.directory):
      try:
        logging.debug('Directory %s does not exist, creating one' % self.directory)
        os.makedirs(self.directory)
      except IOError as err:
        logging.error('Could not create directory %s; reason: %s' % (self.directory, err))
        raise ValueError

    try:
      logging.debug('Binding the socket to %s:%d' % self.addr_port)
      self.socket.bind(self.addr_port)
    except socket.error as err:
      logging.error('Can\'t bind the socket to %s:%d; reason: %s' % (self.addr_port + (err,)))
      raise ValueError

    logging.debug('Socket bound to %s:%d' % self.socket.getsockname())
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    common.close_socket(self.socket)

  def __handle(self, sock, addr):
    try:
      # initial handshake
      # recv from client
      # client_id / request for new client_id
      # client awaits for a confirmation == list of files (control code)
      # client requests for a file
      # server opens an existing file/creates a new file
      # if file exists, send its contents to the client
      # ???
      # profit

      # all client threads in server always sleeping
      # if a client sent its changes to the server, then the receiving thread picks it up, puts the message
      # into a queue, notifies all consumer threads via a conditional variable,
      # upon which one of the consumer threads sends the message to all relevant clients
      #
      # 3 threads for a client on client side?
      pass
    except struct.error as err:
      logging.error('Encountered unpacking error: %s' % err)
    except socket.timeout:
      logging.debug('Client connected from %s:%d timed out' % addr)
    except socket.error as err:
      logging.error('Socket error: %s' % err)
    except IOError as err:
      logging.error('I/O error: %s' % err)
    except MemoryError as err:
      logging.error('Memory error: %s' % err)
    except BaseException as err:
      logging.error('Unkown error: %s' % err)
    finally:
      logging.debug('Closing client connected from %s:%d' % addr)
      common.close_socket(sock)

  def listen(self):
    logging.debug('Setting the client queue to %d' % self.tcp_client_queue)
    self.socket.listen(self.tcp_client_queue)

    logging.debug('Start listening')
    while True:
      try:
        client_sock, client_addr = self.socket.accept() # blocks
        logging.debug('New client connected from %s:%d' % client_addr)
        thread = threading.Thread(target = self.__handle, args = (client_sock, client_addr))
        thread.setDaemon(True)
        thread.start()
      except KeyboardInterrupt:
        logging.debug('Catched SIGINT')
        break