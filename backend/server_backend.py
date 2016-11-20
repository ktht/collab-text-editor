import common, logging, socket, os, threading, struct, db_manager

metainfo = {
  'description' : '{name} {version} %s (%s)'.format(
                  name = 'Collab text editor server', version = '0.0.1', built = '11/11/16'
  )
}

class server:
  tcp_client_queue = 10

  def __init__(self, addr, port, directory):
    logging.debug('Starting %s' % metainfo['description'])

    self.addr_port = (addr, port)
    self.directory = os.path.abspath(directory)
    self.db = None

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

    self.db = db_manager.db_manager(os.path.join(self.directory, 'db.json'))

    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    common.close_socket(self.socket)

  def __handle(self, sock, addr):
    try:
      # initial handshake
      init_args = None
      while True:
        # 1) receive either request for a new id,
        # or initialization of a new session

        while init_args is None:
          init_data = sock.recv(common.ctrl_struct.size)
          if not init_data:
            logging.error("Didn't receive any data from the client")
          unp_init_data = common.ctrl_struct.unpack(init_data)
          init_ctrl, init_pl = unp_init_data
          logging.debug("Received data: %s" % str(unp_init_data))

          if init_ctrl == common.CTRL_REQ_NEW_ID:
            # we have a new user; let's give him/her a new ID
            new_id = self.db.add_user()
            if new_id:
              logging.info("Created a new user w/ ID '%s'" % str(new_id))

              # let the user know its new ID
              p_new_id = common.ctrl_struct.pack(*(common.CTRL_OK, new_id))
              sock.sendall(p_new_id)
            else:
              logging.info("Could not create a new user, aborting connection")
              break
            continue
          elif init_ctrl == common.CTRL_REQ_INIT_SESS:
            # the user requests a new session
            # send a list of available files back
            # the payload user sent is expected to be the user ID
            usr_id = int(init_pl)
            logging.debug("User #ID = '%d' initialized a session, retriveing list of files" % usr_id)
            usr_files = self.db.get_user_files(usr_id)
            if usr_files is None:
              # this fails if the user does not exist in the DB
              logging.debug("User #ID = '%d' is not registered in our DB, cut him/her" % usr_id)
              break
            files_pl = str(common.CTRL_OK) + (common.DELIM * 3) + common.DELIM.join(usr_files)
            sock.sendall(files_pl)

            # wait for the user to respond with a request to either open an existing file
            # or to create a new file; an existing file may be also be owned by another user, which
            # is identified by the user and the file name itself, e.g.
            #     user_id:file_name
            # (otherwise there would be no way to collaboratively edit any files)
            # if the user_id is different from initiator of the session, and the file does not
            # exist (or in future cases, not made public for editing), dismiss the request
            # long story short, expect a file name from the user

            #TODO: create a manager class that deals with file handlers and editing
            fn = common.recv(sock)
            fn_id, fn_loc = fn.split(common.DELIM_ID_FILE)
            fn_id = int(fn_id)
            if fn_id != usr_id:
              logging.debug("User #ID = '%d' requested file '%s' from user #ID = '%d'" % (usr_id, fn_loc, fn_id))
              # request the other user's files
              othr_files = self.db.get_user_files(fn_id)
              if fn not in othr_files:
                logging.debug("User #ID = '%d' requested file '%s' from user #ID = '%d' which does not exist; abort" %
                              (usr_id, fn_loc, fn_id))
                break
              else:
                logging.debug("User #ID = '%d' starts editing file '%s' owned by user #ID = '%d'" %
                              (usr_id, fn_loc, fn_id))
                init_args = (sock, fn, False)
            else:
              logging.debug("User #ID = '%d' requested to open their own file '%s'" % (usr_id, fn_loc))
              if fn not in usr_files:
                logging.debug("User #ID = '%d' requested to create a new file '%s'" % (usr_id, fn_loc))
                init_args = (sock, fn, True)
                # update db accordingly
              else:
                logging.debug("User #ID = '%d' requested to open an existing file '%s'" % (usr_id, fn_loc))
                # open an existing file
                init_args = (sock, fn, False)
              break
          else:
            break
        if init_args is None:
          logging.error("Unauthenticated user?!")
          break

        # create a new thread and attach the file handler manager to it

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