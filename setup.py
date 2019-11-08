from setuptools import setup, find_packages

from ahapiclient.__version__ import __version__

setup(name='ahapiclient',
      version=__version__,
      description='Python AmazingHiring API Client',
      url='https://github.com/AmazingHiring/ahapiclient',
      author='AmazingHiring Dev team',
      author_email='dev@amazinghiring.com',
      packages=['ahapiclient'],
      install_requires=[
          'requests',
      ],
      include_package_data=True)