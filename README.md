# Attention_seq2seq

This directory contains code and resources for a sequence-to-sequence (seq2seq) model with attention mechanisms, implemented for the DA6401 Assignment 3.

## Contents

- **DA6401_A3_attention.ipynb**: Main Jupyter Notebook containing the implementation and experiments with RNN, LSTM, and GRU-based encoder-decoder models with Bahdanau attention. The notebook covers:
  - Data loading and preprocessing using the Dakshina dataset (focused on Hindi transliteration).
  - Custom implementation of GRU, LSTM, and SimpleRNN-based encoders and decoders.
  - Bahdanau attention layer for improved sequence modeling.
  - Training and evaluation routines, including support for hyperparameter tuning and checkpointing.
  - Visualizations and analysis of attention weights.

- **predictions_attention/**: Directory intended for storing model predictions made with attention.

## Quick Start

1. **Dataset Download**: The notebook downloads and extracts the Dakshina dataset (https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar). Make sure you have sufficient disk space before running.
2. **Environment**: The code is designed to run in Google Colab, but can be adapted for local use with appropriate package installations (TensorFlow, Matplotlib, etc.).
3. **Training**: Run the cells in the notebook in sequence to preprocess data, build, and train the attention-based seq2seq models. You can experiment with different RNN types (`GRU`, `LSTM`, or `RNN`), embedding sizes, latent dimensions, and dropout rates.
4. **Results**: Model checkpoints and predictions are saved for further analysis.

## Requirements

- Python 3.7+
- TensorFlow 2.x
- Matplotlib
- WandB (optional, for experiment tracking)
- Other standard Python libraries (os, io, time, numpy, etc.)

## Usage

1. Open the `DA6401_A3_attention.ipynb` notebook.
2. Run all cells to train and evaluate the model.
3. Check the `predictions_attention/` folder for output predictions (if generated during notebook execution).

## References

- [Bahdanau et al., 2014](https://arxiv.org/abs/1409.0473): Neural Machine Translation by Jointly Learning to Align and Translate.
- Dakshina Dataset: [Google Research](https://github.com/google-research-datasets/dakshina)

---
*This directory is part of the DA6401_Assignment3 repository by [prateek122000](https://github.com/prateek122000).*
