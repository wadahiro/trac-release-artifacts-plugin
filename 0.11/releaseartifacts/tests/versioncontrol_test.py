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
from releaseartifacts.versioncontrol import *
from trac.versioncontrol.svn_fs import *
from releaseartifacts.SVGdraw import *

class ComponentManagerStub(object):
    components = {}
    
    def __init__(self):
        self.log = LogStub()

    def component_activated(self, dummy):
        pass

    def get_db_cnx(self):
        return DBStub()
    
    def get_repository(self, authname):
        connector = SubversionConnector(self)
        connector.get_repository('svn', '/Users/wadahiro/workspaces/tracprojects/svn/myproject', authname)
    
class LogStub(object):
    
    def debug(self, msg):
        print "DEBUG:%s" % msg 
        
    def info(self, msg):
        print "INFO:%s" % msg 
        
class RequestStub(object):
    
    def __init__(self, authname):
        self.authname = authname
  
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
        
class SCMManagerTest(unittest.TestCase):

    def setUp(self):
        self.req = RequestStub('admin')
        self.req.base_url = '/milestone'
        self.env = ComponentManagerStub()
        self.env.config = ConfigStub()
        #self.artifact = Artifact(self.env, "milestone", "tag/core-1.0", "ProjectA", "http://example.org/releases/org/example/core/1.0/core-1.0.jar")
        #self.scm_manager = SCMManager(self.env, self.req)

    def test_get_url(self):
        #self.assertEquals('http://example.org/releases/org/example/core/1.0/core-1.0.jar',
        #                   self.artifact.get_url())
        d=drawing()
        #then you create a SVG root element
        s=svg()
        #then you add some elements eg a circle and add it to the svg root element
        #you can supply attributes by using named arguments.
        c=circle(fill='red',stroke='blue', r='10')
        #or by updating the attributes attribute:
        c.attributes['stroke-width']=1
        s.addElement(c)
        #then you add the svg root element to the drawing
        d.setSVG(s)
        #and finaly you xmlify the drawing
        print d.toXml()

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SCMManagerTest, 'test1'))
    return suite

if __name__ == '__main__':
    unittest.main()

