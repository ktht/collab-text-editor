import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

import logging, file_manager, common

if __name__ == '__main__':
  logging.basicConfig(
    level  = logging.DEBUG,
    format = '[%(asctime)s] [%(threadName)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] -- %(message)s',
    stream = sys.stdout
  )

  logging.info('Welcome to file_manager testing; take a seat')

  fn = os.path.join(common.TMP_DIR_TEST, 'test.txt')
  fm = file_manager.file_manager(fn)
  fm.edit(0, common.EDIT_REPLACE, "Replaced line")
  fm.edit(0, common.EDIT_REPLACE, "First line")
  fm.edit(1, common.EDIT_REPLACE, "Second line")
  fm.edit(2, common.EDIT_REPLACE, "Third line")
  fm.edit(1, common.EDIT_DELETE)
  fm.edit(1, common.EDIT_INSERT,  "Between the lines")

  contents = fm.str()
  assert(contents == "First line\nBetween the lines\nThird line")

  logging.info('Fin')