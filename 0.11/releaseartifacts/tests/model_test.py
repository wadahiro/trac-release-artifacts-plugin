# -*- coding: utf-8 -*-

import sys
import os
import re
import unittest

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir + os.sep + '../..'
if not base_dir in sys.path:
    sys.path.insert(0, base_dir)

from releaseartifacts.model import *

class ComponentManagerStub(object):
    components = {}

    def component_activated(self, dummy):
        pass

    def get_db_cnx(self):
        return DBStub()
    
class RequestStub(object):
    pass
  
class ConfigStub(object):
    def get(self, tag, key):
        if key == 'repository.snapshot_url':
            return 'http://localhost:8080/repos-snapshots'
        return 'http://localhost:8080/repos'

class DBStub(object):
    def __init__(self, row=None):
        self.row = row
    
    def cursor(self):
        print "cursor"
        return self
    
    def execute(self, sql , args):
        print "excecute"
        return self
    
    def fetchone(self):
        print "fetchone"
        return self.row 
    
    def commit(self):
        print "commit"
        
class ArtifactTest(unittest.TestCase):

    def setUp(self):
        self.req = RequestStub()
        self.req.base_url = '/milestone'
        self.env = ComponentManagerStub()
        self.env.config = ConfigStub()
        self.artifact = Artifact(self.env, "milestone", "tag/core-1.0", "http://example.org/releases/org/example/core/1.0/core-1.0.jar", "ProjectA")

    def test_get_url(self):
        self.assertEquals('http://example.org/releases/org/example/core/1.0/core-1.0.jar',
                           self.artifact.get_url())

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ArtifactTest, 'test1'))
    return suite

if __name__ == '__main__':
    unittest.main()

