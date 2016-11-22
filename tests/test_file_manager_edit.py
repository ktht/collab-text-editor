import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

import logging, file_manager, common

if __name__ == '__main__':
  logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(threadName)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] -- %(message)s',
    stream=sys.stdout
  )

  logging.info('Welcome to file_manager testing; take a seat')

  fn = os.path.join(common.TMP_DIR_TEST, 'test.txt')
  fm = file_manager.file_manager(fn)
  fm.edit(0, "Replaced line")
  fm.edit(0, "First line")
  fm.edit(1, "Second line")

  logging.info('File contents:')
  contents = fm.str()
  print contents

  assert(contents == "First line\nSecond line")

  logging.info('Fin')