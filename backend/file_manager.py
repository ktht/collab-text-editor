import os, common

class file_manager:

  def __init__(self, fn):
    self.fn = os.path.join(common.TMP_DIR_SERVER, fn.replace(common.DELIM_ID_FILE, os.path.sep))
    self.fd = None

    if not os.path.exists(os.path.dirname(self.fn)):
      os.makedirs(os.path.dirname(self.fn))

    self.fd = open(self.fn, 'a+')

    # with a+ opening mode the stream is positioned at the end of the file; let's seek it to the beginning
    self.fd.seek(0)