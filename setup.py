from setuptools import setup, find_namespace_packages

setup(
    name="imagewriter-ii",
    version="0.1.0",
    packages=find_namespace_packages(include="imagewriter*"),
    python_requires=">=3",
    install_requires=[
        "pyserial"
    ],
    entry_points="""
        [console_scripts]
    """,
)
