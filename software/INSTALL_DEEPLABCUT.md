# Installing DeepLabCut

Official documentation:

- https://deeplabcut.github.io/DeepLabCut/README.html

## Recommended installation

We recommend installing DeepLabCut using a dedicated Conda environment.

### Step 1: Install Miniconda

Download and install Miniconda for your operating system:

https://docs.conda.io/en/latest/miniconda.html

### Step 2: Create a new environment

```bash
conda create -n DEEPLABCUT python=3.12
conda activate DEEPLABCUT
```

### Step 3: Install PyTorch

Install the appropriate version of PyTorch for your CPU or GPU following the official PyTorch instructions:

https://pytorch.org/

### Step 4: Install DeepLabCut

GUI version:

```bash
pip install "deeplabcut[gui]"
```

or headless version

```bash
pip install deeplabcut
```

### Step 5: Test the installation

```bash
python -m deeplabcut
```

The DeepLabCut graphical interface should launch successfully.

---

## Additional resources

- Official installation guide
- User Guide
- FAQ
- Troubleshooting
