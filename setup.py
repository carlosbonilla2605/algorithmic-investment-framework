from setuptools import setup, find_packages

setup(
    name="algorithmic-investment-framework",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'yfinance>=0.2.18',
        'alpha-vantage>=2.3.1',
        'polygon-api-client>=1.12.0',
        'requests>=2.31.0',
        'streamlit>=1.28.0',
        'plotly>=5.15.0'
    ]
)
