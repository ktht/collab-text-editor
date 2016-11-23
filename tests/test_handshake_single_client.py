import sys, os, time
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

import logging, threading, common, time
from server_backend import server
from client_backend import client

test_file = 'test.txt'
test_text = 'some text'
client_id = None

def test_client(*args):
  with client(*args) as c:
    client_id = c.req_id()
    logging.info("Client ID is '%d'" % client_id)
    client_files = c.req_session()
    logging.info("Client files: %s" % str(client_files))
    file_contents = c.req_file(common.DELIM_ID_FILE.join([str(client_id), test_file]))
    logging.info("Current file contents: '%s'" % file_contents)
    time.sleep(1)

    for i in range(4):
      ret_changes = c.send_changes(0, common.EDIT_REPLACE, '%s %d' % (test_text, i))
      if ret_changes:
        logging.info("WOOO, SUCCESS!")
      else:
        logging.error("ERROR!")
      time.sleep(0.5)

  time.sleep(1)

def test_server(*args):
  with server(*args) as s:
    s.listen()

if __name__ == '__main__':
  logging.basicConfig(
    level  = logging.DEBUG,
    format = '[%(asctime)s] [%(threadName)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] -- %(message)s',
    stream = sys.stdout
  )

  test_server_thread = threading.Thread(
    target = test_server,
    name   = 'TestServerThread',
    args   = (common.SERVER_INET_ADDR_DEFAULT, common.SERVER_PORT_DEFAULT, common.TMP_DIR_SERVER)
  )
  test_server_thread.setDaemon(True) # dies with the main thread
  test_server_thread.start()

  time.sleep(1)

  test_client_thread = threading.Thread(
    target = test_client,
    name   = 'TestClientThread',
    args   = (common.SERVER_INET_ADDR_DEFAULT, common.SERVER_PORT_DEFAULT, common.TMP_DIR_CLIENT)
  )
  test_client_thread.start()
  test_client_thread.join()

  logging.debug('Server thread still running...')
  time.sleep(1) # let the server run just a little bit
