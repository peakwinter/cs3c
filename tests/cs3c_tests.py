#!/usr/bin/env python
"""
Basic unit tests for a basic S3 CLI.

Coveo S3 Challenge
"""

import io
import json
import os
import random
import unittest

from click.testing import CliRunner

import cs3c


class CS3BucketTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s3 = cs3c.new_session(
            os.environ["AWS_ACCESS_KEY"],
            os.environ["AWS_SECRET_KEY"]
        )
        cls.runner = CliRunner()

    def setUp(self):
        self.s3.meta.client.create_bucket(
            ACL="private", Bucket="cs3c_test_bucket"
        )

    def tearDown(self):
        for x in self.s3.buckets.all():
            if x.name == "cs3c_test_bucket":
                x.objects.delete()
                self.s3.meta.client.delete_bucket(Bucket=x.name)

    def test_no_print_errors(self):
        result = self.runner.invoke(
            cs3c.list_buckets, ['-f', 'cs3c_test_bucket']
        )
        self.assertEqual(result.exit_code, 0)

    def test_name_filter_success(self):
        result = self.runner.invoke(
            cs3c.list_buckets, ['-j', '-f', 'cs3c_test_bucket']
        )
        result = json.loads(result.output.split("\n")[0])
        self.assertEqual(len(result), 1)

    def test_name_filter_fail(self):
        result = self.runner.invoke(
            cs3c.list_buckets, ['-j', '-f', 'randomstringoeshere']
        )
        result = json.loads(result.output.split("\n")[0])
        self.assertEqual(len(result), 0)


class CS3ObjectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s3 = cs3c.new_session(
            os.environ["AWS_ACCESS_KEY"],
            os.environ["AWS_SECRET_KEY"]
        )
        cls.runner = CliRunner()
        cls.s3.meta.client.create_bucket(
            ACL="private", Bucket="cs3c_test_bucket"
        )

    @classmethod
    def tearDownClass(cls):
        for x in cls.s3.buckets.all():
            if x.name == "cs3c_test_bucket":
                x.objects.delete()
                cls.s3.meta.client.delete_bucket(Bucket=x.name)
                break

    def setUp(self):
        self.size_count = 0
        self.file_count = random.randrange(5, 20)
        for x in range(0, self.file_count):
            size = random.randrange(5, 128)
            self.size_count += size
            data = io.BytesIO(b"x" * size)
            self.s3.meta.client.upload_fileobj(
                data, "cs3c_test_bucket", str(x)
            )

    def tearDown(self):
        for x in self.s3.buckets.all():
            if x.name == "cs3c_test_bucket":
                x.objects.delete()
                break

    def test_no_print_errors(self):
        result = self.runner.invoke(
            cs3c.list_buckets, ['-f', 'cs3c_test_bucket']
        )
        self.assertEqual(result.exit_code, 0)

    def test_file_count(self):
        result = self.runner.invoke(
            cs3c.list_buckets, ['-j', '-f', 'cs3c_test_bucket']
        )
        result = json.loads(result.output.split("\n")[0])
        self.assertEqual(result[0]["totals"]["count"], self.file_count)

    def test_file_sizes(self):
        result = self.runner.invoke(
            cs3c.list_buckets, ['-j', '-f', 'cs3c_test_bucket']
        )
        result = json.loads(result.output.split("\n")[0])
        self.assertEqual(result[0]["totals"]["size"], self.size_count)
