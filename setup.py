from os.path import dirname, join

import setuptools

import model_bakery

setuptools.setup(
    name="model_bakery",
    version=model_bakery.__version__,
    packages=["model_bakery"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=open(join(dirname(__file__), "requirements.txt")).readlines(),
    author="berinfontes",
    author_email="bernardoxhc@gmail.com",
    url="http://github.com/model-bakers/model_bakery",
    license="Apache 2.0",
    description="Smart object creation facility for Django.",
    long_description=open(join(dirname(__file__), "README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="django testing factory python",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Framework :: Django',
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
