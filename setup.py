import setuptools
from os.path import join, dirname

import model_mommy


setuptools.setup(
    name="model_mommy",
    version=model_mommy.__version__,
    packages=["model_mommy"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=open(join(dirname(__file__), 'requirements.txt')).readlines(),
    tests_require=[
        'django>=1.11',
        'pil',
        'tox',
    ],
    test_suite='runtests.runtests',
    author="vandersonmota",
    author_email="vandersonmota@gmail.com",
    url="http://github.com/vandersonmota/model_mommy",
    license="Apache 2.0",
    description="Smart object creation facility for Django.",
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    keywords="django testing factory python",
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
