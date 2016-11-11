#!/usr/bin/env python

import argparse, logging, os, sys, common
from server_backend import server, metainfo

def port_type(port):
  import argparse
  if not port.isdigit():
    raise argparse.ArgumentTypeError('invalid int value: \'%s\'' % str(port))

  port_i = int(port)
  port_range = (2 ** 10, 2 ** 16 - 1)
  if not (port_range[0] <= port_i <= port_range[1]):
    raise argparse.ArgumentTypeError('port not in range [%d, %d]: %s' % (port_range + (port,)))
  return port_i

if __name__ == '__main__':
  logging.basicConfig(
    level  = logging.INFO,
    format = '[%(asctime)s] [%(threadName)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] -- %(message)s',
    stream = sys.stdout
  )
  parser = argparse.ArgumentParser(**dict(metainfo,
    formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position = 30, width = 100)
  ))
  parser.add_argument('-l', '--listenaddr', metavar = 'addr', type = str, default = common.SERVER_INET_ADDR_DEFAULT,
                      help = 'INET address to bind the server socket to')
  parser.add_argument('-p', '--port', metavar = 'port', type = port_type, default = common.SERVER_PORT_DEFAULT,
                      help = 'Port number to bind the server socket to')
  parser.add_argument('-d', '--directory', metavar = 'path', type = str, default = os.path.join(os.getcwd(), '.tmp'),
                      help = 'Directory where to keep the uploaded files')
  parser.add_argument('-v', '--verbose', action = 'store_true', default = False,
                      help='Enable debug output')
  args = parser.parse_args()

  if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

  try:
    with server(args.listenaddr, args.port, args.directory) as s:
      s.listen()
  except Exception as err:
    logging.error("Terminating ...")
    sys.exit(1)

  logging.debug("Exiting ...")