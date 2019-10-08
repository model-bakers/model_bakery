import setuptools
from os.path import join, dirname

import model_bakery


setuptools.setup(
    name="model_bakery",
    version=model_bakery.__version__,
    packages=["model_bakery"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=open(join(dirname(__file__), 'requirements.txt')).readlines(),
    tests_require=[
        'django>=1.11',
        'pil',
        'tox',
    ],
    test_suite='runtests.runtests',
    author="berinfontes",
    author_email="bernardoxhc@gmail.com",
    url="http://github.com/berinhard/model_bakery",
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
