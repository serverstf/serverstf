import setuptools


setuptools.setup(
    name="serverstf",
    version="0.1.0",
    packages=setuptools.find_packages(),
    install_requires=[
        "asyncio-redis",
        "bokeh",
        "geoip2",
        "iso3166",
        "pyramid",
        "pyramid_jinja2",
        "python-valve",
        "python3-openid",
        "venusian",
        "voluptuous",
        "waitress",
        "websockets",
    ],
    extras_require={
        "development": [
            "pylint",
        ],
    },
    entry_points={
        'console_scripts': [
            'serverstf = serverstf.__main__:main',
        ],
    },
)
