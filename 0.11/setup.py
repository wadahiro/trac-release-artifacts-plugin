from setuptools import find_packages, setup

PACKAGE = 'ReleaseArtifactsPlugin'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      author='wadahiro',
      author_email = "wadahiro@gmail.com",
      description = "Manage Release Artifacts.",
      license = "New BSD",
      keywords = 'trac plugin release',
      packages=find_packages(exclude=['*.tests*']),
      package_data = { 'releaseartifacts': ['htdocs/js/*.js','htdocs/css/*.css','htdocs/images/*.gif','templates/*.html'] },
      entry_points = {
          'trac.plugins': [
              'releaseartifacts.web_ui = releaseartifacts.web_ui',
              'releaseartifacts.model = releaseartifacts.model',
              'releaseartifacts.initenv = releaseartifacts.initenv'
          ]
      }
)
