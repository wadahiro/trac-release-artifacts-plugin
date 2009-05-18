# -*- coding: utf-8 -*-

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
import re

class EnvSetup(Component):
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.log.debug('ReleaseArtifactsPlugin environment_created')
        pass

    def environment_needs_upgrade(self, db):
        self.log.debug('ReleaseArtifactsPlugin environment_needs_upgrade')
        cursor = db.cursor()
        try:
            sql = 'SELECT * FROM release_artifact'
            self.log.debug('%s' % sql)
            cursor.execute(sql)
        except Exception,e:
            self.log.warn('%s' % e)
            return True

        return False

    def upgrade_environment(self, db):
        self.log.debug('ReleaseArtifactsPlugin upgrade_environment')

        sql = [
 """CREATE TABLE release_artifact (
         milestone text,
         tag text,
         url text,
         keywords text,
         UNIQUE (milestone, tag)
     )"""
]
        cursor = db.cursor()
        for s in sql:
            try:
                self.log.debug('%s' % s)
                cursor.execute(s)
            except Exception,e:
                self.log.error('%s' % e)
                None
        
        self.log.debug('ReleaseArtifactsPlugin upgrade_environment end.')
