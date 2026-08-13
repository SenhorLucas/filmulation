from setuptools import find_packages, setup

setup(name='filmulation',
      version='0.1.0',
      description='Simulation of analog film photography',
      author='Lucas Viana',
      author_email='lucas.nviana@gmail.com',
      packages=find_packages(),
      package_data={'filmulation': ['data/**/*']},
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'filumation = filmulation.gui.main:main',
              'filmulation-lut = filmulation.cli:run'
          ]
      },
      install_requires=[
          'numpy~=2.1.3',
          'matplotlib~=3.10.0',
          'scipy~=1.14.1',
          'colour-science~=0.4.6',
          'scikit-image~=0.25.0',
          'dotmap~=1.3.30',
          'opt-einsum~=3.4.0',
          'lmfit~=1.3.2',
          'numba~=0.61.0',
          'OpenImageIO~=3.0.3.1',
          'pyfftw~=0.15.0',
      ],
      extras_require={
          'gui': [
              'napari~=0.5.5',
              'magicgui~=0.10.0',
              'pyqt5~=5.15.9',
          ],
      },
      )
