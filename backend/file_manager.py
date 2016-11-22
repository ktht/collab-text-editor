import os, common, logging, threading

class file_manager:

  #TODO: map the file onto a dict and perform the change on dict only
  #      then create another thread that periodically (or upon some trigger) will save the dict to the actual file

  def __init__(self, fn):
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

    if os.path.exists(self.fn) and os.path.isfile(self.fn):
      with open(self.fn, 'r') as f:
        self.lines = dict(enumerate(map(lambda x: x.rstrip('\n'), f.readlines())))
        self.nof_lines = len(self.lines)

    self.fd = open(self.fn, 'w')

  def __del__(self):
    # gracefully close the file
    if not self.fd.closed:
      # this check is valid for current process only
      # but since we're using threading module instead of multiprocessing, this is not an issue
      self.fd.close()

  def str(self):
    return '\n'.join(self.lines.values())

  def chunks(self, chunk_size = common.MAX_PDU_SZ):
    s = self.str()
    for i in range(0, len(s), chunk_size):
      yield s[i:i + chunk_size]

  @common.synchronized("lock")
  def edit(self, line_no, new_line):
    # lock this guy just in case multiple threads edit the file
    # this will never happen, though, b/c there is one thread per file anyways
    # but safety first

    # edits n-th line in place
    logging.debug("Editing %d-th line in file '%s'" % (line_no, self.fn))
    if line_no <= self.nof_lines:
      # replace an existing line or add a new line
      self.lines[line_no] = new_line
      if line_no == self.nof_lines:
        # we added a new line to the file
        self.nof_lines += 1
    else:
      logging.debug('Line number out of bounds!')
      return False

    self.fd.seek(0)
    self.fd.writelines(self.str())
    self.fd.truncate()

    logging.debug('Successfully updated the file')
    return True

