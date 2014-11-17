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
        # A dummy stat queue to dump things into
        cls.stat_queue = s3_parallel_put.JoinableQueue()

    @classmethod
    def tearDownClass(cls):
        cls.connection_patch.stop()

    def setUp(self):
        self.put_queue = mock.MagicMock()
        self.put_queue.get.side_effect = [
            ('key_name', {'content': 'boo'}),
            None,  # cause while loop to break
        ]

    def mock_put(self, bucket, key_name, value):
        """Helper to test that `putter` puts things the way we expect."""
        print bucket, key_name  # DELETEME
        self.last_key_put = mock.MagicMock()
        return self.last_key_put

    def test_no_gzip_option_means_no_gzip_content(self):
        options = mock.MagicMock(
            dry_run=False,
            content_type=False,
            gzip=False,
        )
        s3_parallel_put.putter(self.mock_put, self.put_queue, self.stat_queue, options)
        args, kwargs = self.last_key_put.set_contents_from_string.call_args
        # sanity check
        self.assertEqual(args[0], 'boo')
        headers = args[1]
        self.assertNotIn('Content-Encoding', headers)

    def test_gzip_option_with_zippable_content_means_gzip_content(self):
        options = mock.MagicMock(
            dry_run=False,
            content_type='text/html',
            gzip=True,
            gzip_type=['guess'],
        )
        # sanity check
        self.assertIn(options.content_type, s3_parallel_put.GZIP_CONTENT_TYPES)
        s3_parallel_put.putter(self.mock_put, self.put_queue, self.stat_queue, options)
        args, kwargs = self.last_key_put.set_contents_from_string.call_args
        # assert that the content changed
        self.assertNotEqual(args[0], 'boo')
        headers = args[1]
        self.assertEqual(headers['Content-Type'], options.content_type)
        self.assertEqual(headers['Content-Encoding'], 'gzip')

    def test_gzip_option_with_unzippable_content_means_normal_content(self):
        options = mock.MagicMock(
            dry_run=False,
            content_type='unicorn/candy',
            gzip=True,
            gzip_type=['guess'],
        )
        s3_parallel_put.putter(self.mock_put, self.put_queue, self.stat_queue, options)
        args, kwargs = self.last_key_put.set_contents_from_string.call_args
        # assert that the content did not get compressed
        self.assertEqual(args[0], 'boo')
        headers = args[1]
        self.assertEqual(headers['Content-Type'], options.content_type)
        self.assertNotIn('Content-Encoding', headers)


if __name__ == '__main__':
    unittest.main()
