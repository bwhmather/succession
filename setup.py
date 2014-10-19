from setuptools import setup, find_packages


setup(
    name='succession',
    url='https://github.com/bwhmather/succession',
    version='0.3.1',
    author='Ben Mather',
    author_email='bwhmather@bwhmather.com',
    maintainer='',
    license='BSD',
    description=(
        "A python library providing concurrent push based lazy linked lists"
    ),
    long_description=__doc__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
    ],
    packages=find_packages(),
    package_data={
        '': ['*.*'],
    },
    zip_safe=False,
    test_suite='succession.tests.suite',
)
