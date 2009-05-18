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
            cursor.execute("insert into release_artifact (milestone, tag, url, keywords) values (%s, %s, %s, %s)",
                           (artifact.milestone,
                            artifact.tag,
                            artifact.url,
                            artifact.keywords
                           ))
        db.commit()
    
    @classmethod
    def find_by_milestone_name(cls, env, milestone_name):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("select milestone, tag, url, keywords from release_artifact where milestone = %s",
                        [milestone_name])
        artifacts = []
        
        for milestone, tag, url, keywords in cursor:
            artifact = Artifact(env, milestone, tag, url, keywords)
            artifacts.append(artifact)
            
        return artifacts
    
    @classmethod
    def find_all(cls, env):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("select milestone, tag, url, keywords from release_artifact",
                        [])
        artifacts = []
        
        for milestone, tag, url, keywords in cursor:
            artifact = Artifact(env, milestone, tag, url, keywords)
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
    
    def __init__(self, env, milestone, tag, url, keywords):
        self.env = env
        self.milestone = milestone
        self.tag = tag
        self.url = url
        self.keywords = keywords
        print keywords
        if self.keywords == None:
            self.keywords == ''
        
    def get_url(self):
        return self.url
    
