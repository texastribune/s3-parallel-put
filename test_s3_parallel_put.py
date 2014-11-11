import imp
import unittest

import mock


# HACK to get around s3-parallel-put not being a findable module
# equivalent to something like `import s3-parallel-put`
# http://stackoverflow.com/questions/6811902/import-arbitrary-named-file-as-a-python-module-without-generating-bytecode-file/6811925#6811925
py_source_open_mode = 'U'
py_source_description = ('.py', py_source_open_mode, imp.PY_SOURCE)
with open('s3-parallel-put', py_source_open_mode) as module_file:
    s3_parallel_put = imp.load_module(
        's3-parallel-put', module_file, 's3-parallel-put', py_source_description)


class PutterTest(unittest.TestCase):
    def mock_put(self, bucket, key_name, value):
        print bucket, key_name

    # DELETEME just testing that I can test
    def test_i_can_run_this_thing_trivial(self):
        put_queue = mock.MagicMock()
        put_queue.get.return_value = None
        stat_queue = s3_parallel_put.JoinableQueue()
        s3_parallel_put.putter(self.mock_put, put_queue, stat_queue, object)


if __name__ == '__main__':
    unittest.main()
