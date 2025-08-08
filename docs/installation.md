# Installation guide

## Prerequisites

Before installing `ontograph`, please ensure you have the following tools installed:


| Tool   | Minimum Version | Description                           | Installation Guide                                                           |
| ------ | --------------- | ------------------------------------- | ---------------------------------------------------------------------------- |
| Python | 3.10            | Programming language                  | [Install Python 3](https://docs.python.org/3/using/index.html)               |
| uv     | —               | Python packaging & dependency manager | [Install uv](https://docs.astral.sh/uv/getting-started/installation/)        |
| git    | —               | Version control system                | [Install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) |


!!! tip "Tip"
    If you are missing any of those pre-requisites, **please follow the installation guide in each resource before you continue**.


## Checking prerequisites

Verify that everything is installed by running:

```bash
python --version   # Should be 3.10 or higher
uv --version
git --version
```

## Installation

This package is currently under development. To try it out, you can clone the repository and install it in "editable" mode. This allows you to make changes to the code and have them reflected immediately without reinstalling.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/saezlab/ontograph.git
   ```

2. **Navigate into the project directory:**
   ```bash
   cd ontograph
   ```

3. **Install the package in editable mode using `uv`:**
   ```bash
   uv pip install -e .
   ```

You can now start using `ontograph` in your Python environment. Any changes you make to the source code will take effect immediately.
