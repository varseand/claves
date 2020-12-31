import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="claves",
    version="1.0a4",
    author="Krzysztof Katowicz-Kowalewski",
    author_email="vnd@vndh.net",
    description="Manage your code enclaves on AWS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/varseand/claves",
    packages=[
        "claves",
    ],
    install_requires=[
        "boto3",
        "PyYAML",
    ],
    scripts=[
        "bin/claves",
    ],
    include_package_data=True,
    package_data={
        "": ["data/enclave.yaml"]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires='>=3.6',
)
