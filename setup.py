from setuptools import setup, find_packages


deps = {
    "alchemy": [
        "colorama",
        "factom-api",
        "factom-keys",
        "google-cloud-datastore",
        "numpy",
        "pandas",
        "plotly",
        "plyvel",
        "uvloop",
    ]
}


setup(
    name="alchemy",
    version="0.0.1",
    description="A library of shared code for the PegNet Alchemy node",
    author="Sam Barnes",
    author_email="sambarnes@factom.com",
    url="https://github.com/sambarnes/alchemy",
    keywords=["alchemy", "pegnet", "stablecoin", "blockchain", "factom"],
    license="MIT",
    py_modules=["alchemy"],
    install_requires=deps["alchemy"],
    zip_safe=False,
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
)
