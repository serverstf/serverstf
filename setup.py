import setuptools


setuptools.setup(
    name="serverstf",
    version="0.1.0",
    packages=setuptools.find_packages(),
    install_requires=[
        "asyncio-redis",
        "websockets",
        "pyramid",
        "pyramid_jinja2",
        "python-valve",
        "venusian",
        "voluptuous",
        "waitress",
    ],
)
