"""
setup.py
--------
بعد تثبيت الحزمة (pip install -e .)، هيتوفر أمر `cai` في أي مكان في التيرمنال.
"""

from setuptools import setup, find_packages

setup(
    name="commandai",
    version="1.0.0",
    description="CommandAI (cai) — AI Agent يعمل داخل Terminal لإدارة الأنظمة والمشاريع",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "requests>=2.31.0",
        "cryptography>=42.0.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "cai=cai.ui.shell:main",
        ],
    },
    python_requires=">=3.9",
)
