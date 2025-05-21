# Attention-based Seq2Seq Model

This directory contains the implementation and results of an **Attention-based Sequence-to-Sequence (Seq2Seq) model** for transliteration, as part of DA6401 Assignment 3.

## Contents

- **DA6401_A3_attention.ipynb**  
  Main Jupyter notebook containing the code and experiments for the Attention-based Seq2Seq model. This notebook includes:
  - Data preprocessing and loading (using the Dakshina dataset)
  - Tokenization and tensorization of input/output sequences
  - Model architecture: encoder-decoder with support for LSTM/GRU/RNN and Bahdanau Attention
  - Training and evaluation functions
  - Experiment tracking with Weights & Biases (wandb)

- **predictions_attention/**
  - `success.txt`: Words correctly transliterated by the model during testing.
  - `failure.txt`: Words where the model's transliteration did not match the ground truth.

## How to Use

1. **Dataset**  
   The notebook downloads and extracts the [Dakshina dataset](https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar) automatically.

2. **Requirements**  
   - Python 3.x
   - TensorFlow 2.x
   - Pandas, NumPy, Matplotlib
   - (Optional) [Weights & Biases](https://www.wandb.com/) for experiment tracking

3. **Running the Notebook**
   - Open `DA6401_A3_attention.ipynb` in Jupyter or Google Colab.
   - Run all cells in sequence to preprocess data, train, and evaluate the model.
   - Prediction outputs will be found in the `predictions_attention` directory.

## Model Overview

- **Architecture**  
  The model is a classic encoder-decoder sequence-to-sequence (Seq2Seq) neural network, enhanced with Bahdanau attention. You can choose between LSTM, GRU, or SimpleRNN cells for both encoder and decoder.
- **Task**  
  Transliteration of words from Romanized script to Indic scripts (e.g., Hindi).
- **Evaluation**  
  Results are split into successes and failures for easy analysis.

## Directory Structure

```
Attention_seq2seq/
├── DA6401_A3_attention.ipynb
├── predictions_attention/
│   ├── success.txt
│   └── failure.txt
└── README.md
```

## Citation

- Dakshina Dataset:  
  [https://github.com/google-research-datasets/dakshina](https://github.com/google-research-datasets/dakshina)

## Author

Created by [prateek122000](https://github.com/prateek122000) for DA6401 Assignment 3.

---
