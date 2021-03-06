#-*- coding: utf-8 -*-
from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class
from health_check.backends.base import BaseHealthCheckBackend, ServiceUnavailable
import random
import datetime
from time import sleep
import platform
py_majversion, py_minversion, py_revversion = platform.python_version_tuple()
if py_majversion == '2':
    basestring = basestring
else:
    basestring = (str,bytes)


class StorageHealthCheck(BaseHealthCheckBackend):
    """
    Tests the status of a StorageBakcend. Can be extended to test any storage backend by subclassing:

        class MyStorageHealthCheck(StorageHealthCheck):
            storage = 'some.other.StorageBackend'
        plugin_dir.register(MyStorageHealthCheck)

    storage must be either a string pointing to a storage class (e.g 'django.core.files.storage.FileSystemStorage') or
    a Storage instance.
    """
    storage = None

    def get_storage(self):
        if isinstance(self.storage, basestring):
            return get_storage_class(self.storage)()
        else:
            return self.storage

    def get_file_name(self):
        return 'health_check_storage_test/test-%s-%s.txt' % (datetime.datetime.now(), random.randint(10000,99999))

    def get_file_content(self):
        return b'this is the healthtest file content'

    def check_status(self):
        try:
            # write the file to the storage backend
            storage = self.get_storage()
            file_name = self.get_file_name()
            file_content = self.get_file_content()

            # save the file
            file_name = storage.save(file_name, ContentFile(content=file_content))
            
            # read the file and compare
            f = storage.open(file_name)
            if not storage.exists(file_name):
                raise ServiceUnavailable("File does not exist")

            read_file_contents = f.read()

            if not read_file_contents.decode("utf-8")  == file_content.decode("utf-8") :
                raise ServiceUnavailable("File content doesn't match")

            # delete the file and make sure it is gone
            storage.delete(file_name)

            if storage.exists(file_name):
                raise ServiceUnavailable("File was not deleted")

            return True
        except ServiceUnavailable as service_unavailable_exc:
            raise service_unavailable_exc
        except Exception as exc:
            raise ServiceUnavailable("Unknown exception")