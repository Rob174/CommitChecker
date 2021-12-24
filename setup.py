from setuptools import setup

setup(
  name = 'commitchecker',
  packages = ['commitchecker'], # this must be the same as the name above
  version = '0.1',
  description = 'Check that all code is correctly committed',
  author = 'Robin M',
  author_email = 'robin.128.456@gmail.com',
  url = 'https://github.com/Rob174/CommitChecker',
  download_url = 'https://github.com/Rob174/CommitChecker/0.1',
  keywords = ['commit', 'ai' "git"], 
  classifiers = [],
  install_requires=['tensorflow>=2.7.0'],
)