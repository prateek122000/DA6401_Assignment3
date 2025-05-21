# DA6401 Assignment 3

This repository contains the deliverables for Assignment 3 of DA6401, focusing on deep learning architectures for sequence modeling. The assignment is organized into two main sections:
- **Vanilla Models**: Implements baseline RNN and LSTM models.
- **Attention Models**: Explores attention-based architectures, including Transformer models.

## Repository Structure

```
.
├── attention/
│   └── ... (Jupyter Notebooks and scripts for attention-based models)
├── vanilla/
│   └── ... (Jupyter Notebooks and scripts for vanilla models)
├── data/
│   └── ... (Datasets used for experiments, if any)
└── README.md
```

## Folders

### 1. `vanilla/`
Contains implementations and experiments with traditional sequence models such as:
- **Simple RNNs**
- **LSTMs**
- **GRUs**

These notebooks and scripts serve as baselines for comparison with more advanced models.

### 2. `attention/`
This folder includes:
- **Self-Attention Mechanisms**
- **Transformer Architectures**
- **Comparative Experiments with Vanilla Models**

The notebooks in this directory demonstrate how attention mechanisms improve performance over traditional RNN-based models.

## Getting Started

1. **Clone the Repository**
   ```bash
   git clone https://github.com/prateek122000/DA6401_Assignment3.git
   cd DA6401_Assignment3
   ```

2. **Install Requirements**
   Most of the code runs in Jupyter Notebook environments. You may need the following Python packages:
   - numpy
   - pandas
   - torch
   - tensorflow (if used)
   - matplotlib
   - seaborn
   - scikit-learn
   - jupyter

   Install them via pip:
   ```bash
   pip install numpy pandas torch tensorflow matplotlib seaborn scikit-learn jupyter
   ```

3. **Run the Notebooks**
   - Navigate to either the `vanilla/` or `attention/` folder.
   - Open the relevant notebooks with Jupyter:
     ```bash
     jupyter notebook
     ```

## Results

- Comparative results and analysis can be found at the end of each notebook.
- Refer to `attention/` for performance improvements using attention mechanisms over vanilla models.

## Contributions

This assignment was completed as part of the DA6401 course. Contributions are welcome for further enhancements or new experiments.

## License

This repository is for educational purposes. If you wish to use or distribute the code, please check with the course instructor or the repository owner.

---
For any queries, please contact [prateek122000](https://github.com/prateek122000).
