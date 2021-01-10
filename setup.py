import setuptools
from uNBT import __version__

with open('README.md', 'r', encoding='utf-8') as f:
    readme_text = f.read()

setuptools.setup(
    name='uNBT',
    version=__version__,
    description='Simple NBT manipulation library',
    long_description=readme_text,
    long_description_content_type='text/markdown',
    url='https://bitbucket.org/Metaray/unbt',
    packages=['uNBT'],
    python_requires='>=3.5',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
