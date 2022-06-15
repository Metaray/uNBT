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
    url='https://github.com/Metaray/uNBT',
    packages=['uNBT'],
    package_data={
        '': ['*.pyi', 'py.typed'],
    },
    python_requires='>=3.5',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
