import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'Paste',
    'plaster_pastedeploy',
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_zcml',
    'gunicorn[gevent]',
    'nti.wsgi.ping @ git+ssh://git@github.com/NextThought/nti.wsgi.ping'
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest >= 3.7.4',
    'pytest-cov',
    'pyhamcrest',
    'fudge',
    'zope.testing',
    'zope.testrunner',
    'nti.testing',
    'nti.fakestatsd'
]

docs_require = [
    'sphinx',
    'repoze.sphinx.autointerface',
    'zope.testrunner',
    'nti_sphinx_questions'
]

setup(
    name='nti.app.xrportal',
    version_format='{tag}.dev{commits}+{sha}',
    setup_requires=['very-good-setuptools-git-version'],
    description='XR Content Backend',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='Chris Utz',
    author_email='chris.utz@nextthought.com',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['nti', 'nti.app'],
    include_package_data=True,
    package_data={
        '': ['*.ini','*.mako', '*.zcml'],
    },
    zip_safe=False,
    extras_require={
        'test': tests_require,
        'docs': docs_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = nti.app.xrportal:main',
        ]
    },
)
