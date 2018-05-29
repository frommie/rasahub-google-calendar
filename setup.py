from setuptools import setup, find_packages

install_requires = [
    'rasahub',
    'authlib',
    'flask',
    'google-api-python-client'
]

tests_requires = [
]

extras_requires = {
    'test': tests_requires
}

setup(name='rasahub-google-calendar',
      version='0.3.1',
      description='Rasa connector for Google Calendar',
      url='http://github.com/frommie/rasahub-google-calendar',
      author='Christian Frommert',
      author_email='christian.frommert@gmail.com',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development',
      ],
      keywords='rasahub',
      packages=find_packages(exclude=['docs', 'tests']),
      install_requires=install_requires,
      tests_require=tests_requires,
      extras_require=extras_requires,
)
