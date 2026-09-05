# Snakemake instructions

## Installation

Installation using conda:
```
conda create -n teaching-ai-to-read-mouse-behavior -f=environment.yaml
```

Snakemake should install all environments automatically except `simba`. We need to install this environment ourselves.

To install `simba` on macOS, follow the instructions to build xgboost from source [here](https://xgboost.readthedocs.io/en/stable/build.html). Then run this to add the libraries to the environment and install:

```
CONDA_SUBDIR=osx-64 conda create -n simba python=3.10 pip
conda activate simba

mkdir -p "$CONDA_PREFIX/xgboost"
cp path/to/xgboost/lib/libxgboost.dylib \
   "$CONDA_PREFIX/xgboost/libxgboost.dylib"

CONDA_SUBDIR=osx-64 conda install numba==0.63.0 llvmlite
pip install simba-uw-tf-dev
```

On other machines, you can just run:

```
conda create -n simba python=3.10 pip
pip install simba-uw-tf-dev
```

## Usage 

Put your videos in `input/videos/*.avi`.

To run the default rule `all`:

```
snakemake --cores 2 --use-conda
```
