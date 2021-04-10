from os.path import abspath, dirname, join

import setuptools

about: dict = {}
here = abspath(dirname(__file__))
with open(join(here, "model_bakery", "__about__.py")) as f:  # type: ignore
    exec(f.read(), about)

setuptools.setup(
    name="model_bakery",
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__url__"],
    license=about["__license__"],
    packages=["model_bakery"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=open(join(here, "requirements.txt")).readlines(),
    description="Smart object creation facility for Django.",
    long_description=open(join(dirname(__file__), "README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="django testing factory python",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
