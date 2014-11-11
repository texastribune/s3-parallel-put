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
    last_key_put = None

    @classmethod
    def setUpClass(cls):
        # Make sure no actual s3 connections are made
        cls.connection_patch = mock.patch.object(s3_parallel_put, 'S3Connection')
        mock_connection = cls.connection_patch.start()
        mock_connection.return_value.get_bucket.return_value = 'mock-bucket'

    @classmethod
    def tearDownClass(cls):
        cls.connection_patch.stop()

    def mock_put(self, bucket, key_name, value):
        print bucket, key_name
        self.last_key_put = mock.MagicMock()
        return self.last_key_put

    # DELETEME just testing that I can test
    def test_i_can_run_this_thing_trivial(self):
        put_queue = mock.MagicMock()
        put_queue.get.return_value = None
        stat_queue = s3_parallel_put.JoinableQueue()
        s3_parallel_put.putter(self.mock_put, put_queue, stat_queue, object)

    def test_mock_queues(self):
        put_queue = mock.MagicMock()
        put_queue.get.side_effect = [
            ('key_name', {'content': 'boo'}),
            None,  # cause while loop to break
        ]
        stat_queue = s3_parallel_put.JoinableQueue()
        options = mock.MagicMock(
            dry_run=False,
            content_type=False,
            gzip=False,
        )
        s3_parallel_put.putter(self.mock_put, put_queue, stat_queue, options)
        args, kwargs = self.last_key_put.set_contents_from_string.call_args
        # sanity check
        self.assertEqual(args[0], 'boo')
        headers = args[1]
        self.assertNotIn('Content-Encoding', headers)


if __name__ == '__main__':
    unittest.main()
