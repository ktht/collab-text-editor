import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

import logging, threading, common, time
from server_backend import server
from client_backend import client

def test_client(*args):
  with client(*args) as c:
    c.req_id()

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
    args = (common.SERVER_INET_ADDR_DEFAULT, common.SERVER_PORT_DEFAULT, common.TMP_DIR_SERVER)
  )
  test_server_thread.setDaemon(True)
  test_server_thread.start()

  time.sleep(1)

  test_client_thread = threading.Thread(
    target = test_client,
    args = (common.SERVER_INET_ADDR_DEFAULT, common.SERVER_PORT_DEFAULT, common.TMP_DIR_CLIENT)
  )
  test_client_thread.start()
  test_client_thread.join()