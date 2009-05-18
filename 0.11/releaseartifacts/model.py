# -*- coding: utf-8 -*-

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.resource import ResourceNotFound
from trac.ticket.model import Milestone
from trac.versioncontrol import Changeset
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol import Changeset, Node
import re

class ArtifactManager:
    
    @classmethod
    def update_all(cls, env, artifacts, milestone_old_name=''):
        db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('delete from release_artifact where milestone = %s',
                        [milestone_old_name])
        
        for artifact in artifacts:
            cursor.execute("insert into release_artifact (milestone, scm_path, customer_name, url) values (%s, %s, %s, %s)",
                           (artifact.milestone,
                            artifact.scm_path,
                            artifact.customer_name,
                            artifact.url))
        db.commit()
    
    @classmethod
    def find_by_milestone_name(cls, env, milestone_name):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("select milestone, scm_path, customer_name, url from release_artifact where milestone = %s",
                        [milestone_name])
        artifacts = []
        
        for milestone, scm_path, customer_name, url in cursor:
            artifact = Artifact(env, milestone, scm_path, customer_name, url)
            artifacts.append(artifact)
            
        return artifacts
    
    @classmethod
    def find_by_group(cls, env, search_customer_name):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("select milestone, scm_path, customer_name, url from release_artifact where group = %s",
                        [search_customer_name])
        artifacts = []
        
        for milestone, scm_path, customer_name, url in cursor:
            artifact = Artifact(env, milestone, scm_path, customer_name, url)
            artifacts.append(artifact)
            
        return artifacts
    
    @classmethod
    def find_all(cls, env):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("select milestone, scm_path, customer_name, url from release_artifact",
                        [])
        artifacts = []
        
        for milestone, scm_path, customer_name, url in cursor:
            artifact = Artifact(env, milestone, scm_path, customer_name, url)
            artifacts.append(artifact)
            
        return artifacts
        
    @classmethod
    def delete(cls, env, milestone_old_name):
        db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('delete from release_artifact where milestone = %s',
                        [milestone_old_name])
        db.commit()
        
class Artifact:
    
    def __init__(self, env, milestone, scm_path, customer_name, url):
        self.env = env
        self.milestone = milestone
        self.scm_path = scm_path
        self.customer_name = customer_name
        self.url = url
        print customer_name
        if self.customer_name == None:
            self.customer_name == ''
        
    def get_url(self):
        return self.url
    
