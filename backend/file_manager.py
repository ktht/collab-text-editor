import os, common, logging, threading

class file_manager:

  def __init__(self, fn):
    '''Initializes the file_manager instance
    :param fn: string, FileName, which consist of the owner and the file name itself

    The client's files are stored in the directory
      <default server directory>/<file creator's ID>/<file name>
    '''
    self.fn = os.path.join(common.TMP_DIR_SERVER, fn.replace(common.DELIM_ID_FILE, os.path.sep))
    self.fd = None
    self.lock = threading.Lock()
    self.lines = {}

    parent_dir = os.path.dirname(self.fn)
    if not os.path.exists(parent_dir):
      logging.debug("Directory '%s' does not exist, creating it" % parent_dir)
      os.makedirs(parent_dir)

    logging.debug("Opening file '%s' for reading" % self.fn)
    self.lines = {}
    self.nof_lines = 0

    # map line numbers and lines themselves to a dictionary
    if os.path.exists(self.fn) and os.path.isfile(self.fn):
      with open(self.fn, 'r') as f:
        self.lines = dict(enumerate(map(lambda x: x.rstrip('\n'), f.readlines())))
        self.nof_lines = len(self.lines)

    self.fd = open(self.fn, 'w')

  def __update__(self):
    '''Updates the file with the contents of the dictionary representing the file
    :return: None

    Might throw, though
    '''
    self.fd.seek(0)
    self.fd.writelines(self.str())
    self.fd.truncate()

  def close(self):
    '''Gracefully close the file
    :return: None

    Pro tip: make sure the function is called if the process is about to exit (use atexit.register())
    __del__ won't work b/c we'd rely on Python's garbage collector or we should del explicitly
    '''
    if not self.fd.closed:
      # write the changes back to the file
      # this is needed b/c if the user opens a file but doesn't change it
      # then due to the opening mode of 'w' the file will be blank
      # in order to overcome this, we must write the file explicitly again
      self.__update__()
      # this check is valid for current process only
      # but since we're using threading module instead of multiprocessing, this is not an issue
      self.fd.close()

  def str(self):
    '''Get file contents as a string
    :return: string, The file contents
    '''
    return '\n'.join(self.lines.values())

  def edit(self, line_no, action, new_line = '', id = None):
    '''Edits a line in the file represented by a dictionary
    :param line_no:  int, The line nr to be edited (line numbers start from 0)
    :param action:   int, valid values are common.EDIT_REPLACE, common.EDIT_INSERT and common.EDIT_DELETE
    :param new_line: string, The replacement line (ignored if `action' is set to common.EDIT_DELETE)
    :param id:       int, ID of the client that issued the change; ignored

    :return: True, if the file modification was successful
             False, if the method encountered inconsistencies
                    (i.e. the line number requested was out of bounds, that is it exceeded the total
                     number of lines in the file)
    Note that if `line_no' is equal to the number of lines in the file, the line will be appended at the end of file
    '''

    # edits n-th line in place
    logging.debug("Editing %d-th line in file '%s' with action '%d'" %
                  (line_no, self.fn, action))
    if line_no <= self.nof_lines:
      if action == common.EDIT_REPLACE:
        # replace an existing line or add a new line
        self.lines[line_no] = new_line
        if line_no == self.nof_lines:
          # we added a new line to the file
          self.nof_lines += 1
      elif action == common.EDIT_INSERT:
        if line_no in self.lines:
          # shift all lines by one row below the line which was inserted
          for line_no_new in range(self.nof_lines, line_no, -1):
            self.lines[line_no_new] = self.lines[line_no_new - 1]
        self.lines[line_no] = new_line
        self.nof_lines += 1
      elif action == common.EDIT_DELETE:
        del self.lines[line_no]
        line_no_next = line_no + 1
        if line_no_next in self.lines:
          for line_no_new in range(line_no_next, self.nof_lines):
            # shift all lines by one row above the line which was deleted
            self.lines[line_no_new - 1] = self.lines[line_no_new]
        del self.lines[self.nof_lines - 1]
        self.nof_lines -= 1
      else:
        logging.debug("No such control code in file editing: %s" % str(action))
    else:
      logging.debug('Line number out of bounds!')
      return False

    try:
      self.__update__()
    except IOError as err:
      logging.debug("Caught an I/O error: %s" % err)
      return False
    except BaseException as err:
      logging.debug("Unknown error: %s" % err)
      return False

    logging.debug('Successfully updated the file')
    return True

