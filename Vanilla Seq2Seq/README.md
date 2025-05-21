# Vanilla Seq2Seq

This directory contains the implementation and results of a **Vanilla Sequence-to-Sequence (Seq2Seq) model** for transliteration, as part of DA6401 Assignment 3.

## Contents

- **DL_A3_Vanilla.ipynb**  
  Main Jupyter notebook containing the code and experiments for the Vanilla Seq2Seq model. This notebook covers:
  - Data preprocessing (Dakshina dataset download and preparation)
  - Tokenization and tensorization of input/output sequences
  - Model architecture: configurable encoder-decoder with LSTM/GRU/RNN options
  - Training (manual and with Weights & Biases sweeps)
  - Inference and evaluation functions

- **predictions_vanilla/**
  - `success_predictions.txt`: Words correctly transliterated by the model during testing.
  - `failure_predictions.txt`: Words where the model's transliteration did not match the ground truth.

## How to Use

1. **Dataset**:  
   The notebook downloads and extracts the [Dakshina dataset](https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar) automatically.

2. **Requirements**:  
   - Python 3.x
   - TensorFlow 2.x
   - Pandas, NumPy
   - (Optional) [Weights & Biases](https://www.wandb.com/) for experiment tracking

3. **Running the Notebook**:
   - Open `DL_A3_Vanilla.ipynb` in Jupyter or Google Colab.
   - Run all cells in sequence.
   - Training and evaluation will produce prediction logs in the `predictions_vanilla` directory.

## Model Overview

- **Architecture**:  
  Classic encoder-decoder design using RNNs (LSTM, GRU, or SimpleRNN), with configurable layers, embedding dimensions, and dropout.
- **Task**:  
  Transliteration of words from Romanized script to native Indic scripts (e.g., Hindi).
- **Evaluation**:  
  Results are split into successes and failures for easy analysis.

## Directory Structure

```
Vanilla Seq2Seq/
├── DL_A3_Vanilla.ipynb
├── predictions_vanilla/
│   ├── success_predictions.txt
│   └── failure_predictions.txt
└── README.md
```

## Citation

- Dakshina Dataset:  
  [https://github.com/google-research-datasets/dakshina](https://github.com/google-research-datasets/dakshina)

## Author

Created by [prateek122000](https://github.com/prateek122000) for DA6401 Assignment 3.

---
