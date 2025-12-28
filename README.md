# SkillCorner X PySport Analytics Cup
This repository contains the submission template for the SkillCorner X PySport Analytics Cup **Research Track**. 
Your submission for the **Research Track** should be on the `main` branch of your own fork of this repository.

Find the Analytics Cup [**dataset**](https://github.com/SkillCorner/opendata/tree/master/data) and [**tutorials**](https://github.com/SkillCorner/opendata/tree/master/resources) on the [**SkillCorner Open Data Repository**](https://github.com/SkillCorner/opendata).

## Submitting
Make sure your `main` branch contains:
1. A single Jupyter Notebook in the root of this repository called `submission.ipynb`
    - This Juypter Notebook can not contain more than 2000 words.
    - All other code should also be contained in this repository, but should be imported into the notebook from the `src` folder.
2. An abstract of maximum 500 words that follows the **Research Track Abstract Template**.
    - The abstract can contain a maximum of 2 figures, 2 tables or 1 figure and 1 table.
3. Submit your GitHub repository on the [Analytics Cup Pretalx page](https://pretalx.pysport.org)

Finally:
- Make sure your GitHub repository does **not** contain big data files. The tracking data should be loaded directly from the [Analytics Cup Data GitHub Repository](https://github.com/SkillCorner/opendata).For more information on how to load the data directly from GitHub please see this [Jupyter Notebook](https://github.com/SkillCorner/opendata/blob/master/resources/getting-started-skc-tracking-kloppy.ipynb).
- Make sure the `submission.ipynb` notebook runs on a clean environment.

_⚠️ Not adhering to these submission rules and the [**Analytics Cup Rules**](https://pysport.org/analytics-cup/rules) may result in a point deduction or disqualification._

---

## Set Up Environment

Python **3** is required. Please make sure you have ```pip``` installed so that you can install all of the relevant packages for this repo.

### Create & Activate Virtual Environment

We recommend that you create a clean new virtual environment to prevent any conflicts

On **Mac**, open terminal and run the following set of commands:

```bash
python3 -m venv venv

# specify version (I prefer to work with Python 3.12)
python3.12 -m venv venv
```
**Note:** I prefer to use Python 3.12, but Python3+ should suffice. Please try Python 3.12 first.

Activate environment

```bash
source venv/bin/activate
```

On, **Windows**, open Command Prompt:

```bash
python -m venv .venv

# specify version (I prefer to work with Python 3.12)
py -3.12 -m venv .venv
```
**Note:** I prefer to use Python 3.12, but Python3+ should suffice. Please try Python 3.12 first.

```bash
.venv\Scripts\activate.bat
```

### Install Requirements

```bash
pip install -r requirements.txt
```

## Research Track Abstract
#### Introduction

#### Methods

#### Results

#### Conclusion
