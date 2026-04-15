from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="asyngram",
    version="0.1.2",
    author="Musa ibn Atabek Sadullah",
    author_email="sadullayevmusobek12@gmail.com",
    description="Developer-friendly async Telegram Bot Framework. from Sadullayev Musobek Otabek",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/telegrampy/telegrampy",
    packages=find_packages(exclude=["tests*", "examples*"]),
    python_requires=">=3.10",
    install_requires=[
        "aiohttp>=3.9.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "redis": ["redis>=5.0.0"],
        "sqlalchemy": ["sqlalchemy[asyncio]>=2.0.0"],
        "all": [
            "redis>=5.0.0",
            "sqlalchemy[asyncio]>=2.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: AsyncIO",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="telegram bot async framework aiogram",
    project_urls={
        "Documentation": "https://telegrampy.readthedocs.io",
        "Source": "https://github.com/telegrampy/telegrampy",
        "Tracker": "https://github.com/telegrampy/telegrampy/issues",
    },
)