import json, logging, os, threading, common

class db_manager:
  '''Database manager

  Manages user IDs and files associated with the users.
  The DB is stored in JSON format, which is updated whenever a new user or a new file is added.
  '''

  #TODO: add more descriptive return codes than boolean's True/False

  KEY_ID         = 'ID'
  KEY_FILES      = 'files'
  KEY_FILENAME   = 'filename'
  KEY_VISIBILITY = 'visibility'

  def __init__(self, json_filename):
    logging.debug('Starting user manager')
    self.json_filename = json_filename
    self.lock = threading.Lock()

    if not os.path.isfile(self.json_filename):
      logging.debug("DB file '%s' does not exists, creating one" % self.json_filename)
      if not os.path.exists(os.path.dirname(self.json_filename)):
        os.makedirs(os.path.dirname(self.json_filename))
      try:
        with open(self.json_filename, 'w') as f:
          f.write(json.dumps([], indent = 2))
      except IOError:
        logging.debug("Could not write the DB file to '%s'" % self.json_filename)
        raise Exception # possibly a bad style

    # read the database; store the db at all times and update in place
    self.db = []
    with open(self.json_filename, 'r') as f:
      self.db = json.load(f)

    # also keep the list of user IDs
    self.ids = [x[db_manager.KEY_ID] for x in self.db]

  def get_user_files(self, user_id):
    '''Retrieves filenames associated with a user if it's present in the DB
    :param user_id: int?, the unique user identification number
    :return: None, if either the DB file is not present, or
                   if the user metadata is missing in the database
             string list, file list
    '''
    if user_id not in self.ids:
      logging.debug("No such user: '%s'" % str(user_id))
      return None

    for entry in self.db:
      if user_id == entry[db_manager.KEY_ID]:
        logging.debug("Found the user '%s' metadata" % str(user_id))
        return entry[db_manager.KEY_FILES]

    logging.debug("Database corruption?")
    return None

  @common.synchronized("lock")
  def add_user_file(self, user_id, new_file, visibility):
    '''Add user to the JSON DB
      :param user_id:    int, The identification number of the new user
      :param new_file:   string, The new file owned by the user
      :param visibility, int, Tells whether the file is made for public editing (equals to common.FILEMODE_PUBLIC)
                              or for private editing only (equals to common.FILEMODE_PRIVATE)
      :return: True, if the addition was successful,
               False otherwise
      '''
    if not new_file:
      logging.debug("Empty file name given")
      return False

    if user_id not in self.ids:
      logging.debug("User '%s' does not exist in our DB" % str(user_id))
      return False

    new_file_locator = common.DELIM_ID_FILE.join([str(user_id), new_file])
    entry_updated = False
    for entry in self.db:
      if entry[db_manager.KEY_ID] == user_id:
        if new_file_locator in entry[db_manager.KEY_FILES]:
          logging.debug("File '%s' already exists under the user, aborting" % new_file)
          return False
        entry[db_manager.KEY_FILES].append({
          db_manager.KEY_FILENAME   : new_file_locator,
          db_manager.KEY_VISIBILITY : visibility,
        })
        entry_updated = True
        logging.debug("Successfully associated the file '%s' with user '%s'" % \
                      (new_file, str(user_id)))
        break

    # update the DB
    if entry_updated:
      try:
        with open(self.json_filename, 'w') as f:
          f.write(json.dumps(self.db, indent = 2))
      except IOError:
        logging.debug("Could not open file '%s' for writing" % self.json_filename)
        return False
      logging.debug("Database has been updated")
      return True

    return False

  @common.synchronized("lock")
  def add_user(self):
    '''Add user to the JSON DB
      :return: the new user_id, if the addition was successful,
               None in case of an error
      '''
    # generate a new user ID by incrementing the largest ID by 2
    new_id = max(self.ids) + 1 if len(self.ids) > 0 else 1
    new_entry = { db_manager.KEY_ID : new_id, db_manager.KEY_FILES : [] }

    self.ids.append(new_id)
    self.db.append(new_entry)

    try:
      with open(self.json_filename, 'w') as f:
        f.write(json.dumps(self.db, indent = 2))
    except IOError:
      logging.debug("Could not write the new user to the DB")
      self.ids.remove(new_id)
      self.db.remove(new_entry)

    return new_id if new_id in self.ids else None