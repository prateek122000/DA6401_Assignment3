# -*- coding: utf-8 -*-


from google.colab import files
uploaded = files.upload()

'''
Imports
'''
!pip install uniseg

import tensorflow as tf

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import unicodedata
import re
import numpy as np
import os
import io
import time
import random
import shutil
from matplotlib.font_manager import FontProperties
import shutil
#HTMl library to generate the connectivity html file
from IPython.display import HTML as html_print
from IPython.display import display

'''
Downloading the dataset
'''
# Download the dataset
!curl https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar --output daksh.tar
# Extract the downloaded tar file
!tar -xvf  'daksh.tar'
# Set the file paths to train, validation and test dataset
#train_path
train_file_path=os.path.join(os.getcwd(),"dakshina_dataset_v1.0","hi","lexicons","hi.translit.sampled.train.tsv")
#validation_path
vaildation_file_path = os.path.join(os.getcwd(),"dakshina_dataset_v1.0","hi","lexicons","hi.translit.sampled.dev.tsv")
#test_path
test_file_path = os.path.join(os.getcwd(),"dakshina_dataset_v1.0","hi","lexicons","hi.translit.sampled.test.tsv")

"""# 🔤 Character-Level Word Preprocessing Pipeline


"""

'''
Preprocesses a word by adding start and end characters.
'''
def word_process(word):
  word = '\t' + word + '\n'
  return word

'''
Reads lines from a file and returns them as a list.
'''
def read_lines(path):
  file = io.open(path, encoding='UTF-8')
  text = file.read()
  lines = text.strip().split('\n')
  return lines

'''
Processes a line and returns a list of processed words.
'''
def process_line(line):
  parts = line.split('\t')
  new_parts = []
  # Skip the last part (usually empty or label)
  for i in range(len(parts) - 1):
    processed_word = word_process(parts[i])
    new_parts.append(processed_word)
  return new_parts

'''
Creates pairs of target and input words.
'''
def create_dataset(path):
  lines = read_lines(path)
  all_pairs = []
  for line in lines[:-1]:
    pair = process_line(line)
    all_pairs.append(pair)

  input_words = []
  target_words = []

  for pair in all_pairs:
    target_words.append(pair[0])
    input_words.append(pair[1])

  return input_words, target_words

'''
Creates a character-level tokenizer.
'''
def build_tokenizer():
  tokenizer = tf.keras.preprocessing.text.Tokenizer(filters='', char_level=True)
  return tokenizer

'''
Tokenizes and pads the given list of words.
'''
def tokenize(lang):
  tokenizer = build_tokenizer()
  tokenizer.fit_on_texts(lang)

  sequences = tokenizer.texts_to_sequences(lang)
  padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(sequences, padding='post')

  return padded_sequences, tokenizer

'''
Loads the dataset, returning tokenized and padded input/output tensors and their tokenizers.
'''
def load_dataset(path):
  input_lang, output_lang = create_dataset(path)

  input_tensor, input_tokenizer = tokenize(input_lang)
  output_tensor, output_tokenizer = tokenize(output_lang)

  return input_tensor, output_tensor, input_tokenizer, output_tokenizer

"""## Reading the Training Dataset

This section reads the full training dataset using the `load_dataset` function defined earlier. It also calculates the maximum sequence lengths of the input and target tensors, which are useful for building the model.

"""

'''
Reading the training dataset entirely
'''
# Use the entire training dataset file
input_tensor_train, target_tensor_train, inp_lang, targ_lang = load_dataset(train_file_path)

# Calculate max_length of the target tensors
max_length_targ, max_length_inp = target_tensor_train.shape[1], input_tensor_train.shape[1]

"""# Sequence Encoder Classes
Defines TensorFlow-based encoder classes for sequence models using GRU, LSTM, and Simple RNN layers. Each class includes an embedding layer, the recurrent layer, and hidden state initialization.


"""

import tensorflow as tf

'''
Class - GRU Encoder
'''
class GRU_Encoder(tf.keras.Model):
  def __init__(self, vocab_size, embedding_dim, enc_units, batch_sz, dropout=0):
    super(GRU_Encoder, self).__init__()
    self.batch_sz = batch_sz
    self.enc_units = enc_units
    self.embedding = self.create_embedding_layer(vocab_size, embedding_dim)
    self.gru = self.create_gru_layer(enc_units, dropout)

  # Create embedding layer
  def create_embedding_layer(self, vocab_size, embedding_dim):
    return tf.keras.layers.Embedding(vocab_size, embedding_dim)

  # Create GRU layer
  def create_gru_layer(self, units, dropout):
    return tf.keras.layers.GRU(
      units,
      return_sequences=True,
      return_state=True,
      recurrent_initializer='glorot_uniform',
      dropout=dropout
    )

  # Forward pass through the encoder
  def call(self, x, hidden):
    x = self.embedding(x)
    output, state = self.gru(x, initial_state=hidden)
    return output, state

  # Initialize hidden state to zeros
  def initialize_hidden_state(self):
    return tf.zeros((self.batch_sz, self.enc_units))


'''
Class - LSTM Encoder
'''
class LSTM_Encoder(tf.keras.Model):
  def __init__(self, vocab_size, embedding_dim, enc_units, batch_sz, dropout=0):
    super(LSTM_Encoder, self).__init__()
    self.batch_sz = batch_sz
    self.enc_units = enc_units
    self.embedding = self.create_embedding(vocab_size, embedding_dim)
    self.lstm = self.create_lstm(enc_units, dropout)

  # Embedding layer
  def create_embedding(self, vocab_size, embedding_dim):
    return tf.keras.layers.Embedding(vocab_size, embedding_dim)

  # LSTM layer
  def create_lstm(self, units, dropout):
    return tf.keras.layers.LSTM(
      units,
      return_sequences=True,
      return_state=True,
      recurrent_initializer='glorot_uniform',
      dropout=dropout
    )

  # Forward pass through the LSTM encoder
  def call(self, x, hidden, cell_state):
    x = self.embedding(x)
    output, h_state, c_state = self.lstm(x, initial_state=[hidden, cell_state])
    return output, h_state, c_state

  # Initialize both hidden and cell state
  def initialize_hidden_state(self):
    hidden = tf.zeros((self.batch_sz, self.enc_units))
    cell = tf.zeros((self.batch_sz, self.enc_units))
    return hidden, cell


'''
Class - Simple RNN Encoder
'''
class RNN_Encoder(tf.keras.Model):
  def __init__(self, vocab_size, embedding_dim, enc_units, batch_sz, dropout=0):
    super(RNN_Encoder, self).__init__()
    self.batch_sz = batch_sz
    self.enc_units = enc_units
    self.embedding = self.init_embedding(vocab_size, embedding_dim)
    self.rnn = self.init_rnn(enc_units, dropout)

  # Set up embedding
  def init_embedding(self, vocab_size, embedding_dim):
    return tf.keras.layers.Embedding(vocab_size, embedding_dim)

  # Set up RNN
  def init_rnn(self, units, dropout):
    return tf.keras.layers.SimpleRNN(
      units,
      return_sequences=True,
      return_state=True,
      recurrent_initializer='glorot_uniform',
      dropout=dropout
    )

  # Forward pass
  def call(self, x, hidden):
    x = self.embedding(x)
    output, final_state = self.rnn(x, initial_state=hidden)
    return output, final_state

  # Hidden state initialization
  def initialize_hidden_state(self):
    return tf.zeros((self.batch_sz, self.enc_units))

'''
Attention class (Bhadanau Attention) refernce for the attention  - https://arxiv.org/abs/1409.0473
'''
class BahdanauAttention(tf.keras.layers.Layer):
  #initialization
  def __init__(self, units):
    super(BahdanauAttention, self).__init__()
    self.W1 = tf.keras.layers.Dense(units)  #W_1
    self.W2 = tf.keras.layers.Dense(units)  #W_2
    self.V = tf.keras.layers.Dense(1)       #V

  '''
  call function genrating the context vector and the attention weights
  '''
  def call(self, query, values):
    '''
    shape of query hidden state == (batch_size, hidden size)
    shape of query_with_time_axis == (batch_size, 1, hidden size)
    shape of values  == (batch_size, max_len, hidden size)
    '''
    #To broadcast addition along the time axis to calculate the score
    query_with_time_axis = tf.expand_dims(query, 1)

    # shape of score == (batch_size, max_length, 1)
    # shape of the tensor before applying self.V is (batch_size, max_length, units)
    score = self.V(tf.nn.tanh(
        self.W1(query_with_time_axis) + self.W2(values)))

    # shape of attention_weights == (batch_size, max_length, 1)
    #generating the attention weights
    attention_weights = tf.nn.softmax(score, axis=1)

    # context_vector shape after sum == (batch_size, hidden_size)
    #generating the context vector
    context_vector = attention_weights * values
    context_vector = tf.reduce_sum(context_vector, axis=1)

    #returning the context vector and the attention weights
    return context_vector, attention_weights

"""#Decoder Classes

Refactored TensorFlow decoders with attention for seq2seq tasks.

---


"""

'''
GRU Decoder Implementation - Refactored
'''
class GRU_Decoder(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, dec_units, batch_sz, dropout=0):
        super(GRU_Decoder, self).__init__()
        # Store configuration parameters
        self.batch_size = batch_sz
        self.decoder_units = dec_units
        self.vocabulary_size = vocab_size
        self.embed_dimensions = embedding_dim

        # Initialize all layers in __init__ to avoid variable creation issues
        self.word_embeddings = tf.keras.layers.Embedding(
            input_dim=self.vocabulary_size,
            output_dim=self.embed_dimensions
        )

        self.gru_cell = tf.keras.layers.GRU(
            units=self.decoder_units,
            return_sequences=True,
            return_state=True,
            recurrent_initializer='glorot_uniform',
            dropout=dropout
        )

        self.output_projection = tf.keras.layers.Dense(units=self.vocabulary_size)
        self.attention_layer = BahdanauAttention(self.decoder_units)

    def _compute_context_vector(self, current_hidden, encoder_outputs):
        """Extract attention context and weights"""
        context_vec, attn_weights = self.attention_layer(current_hidden, encoder_outputs)
        return context_vec, attn_weights

    def _prepare_input_sequence(self, input_tokens, context_vector):
        """Process input tokens and concatenate with context"""
        # Step 1: Convert tokens to embeddings
        embedded_input = self.word_embeddings(input_tokens)

        # Step 2: Expand context vector dimensions
        expanded_context = tf.expand_dims(context_vector, axis=1)

        # Step 3: Concatenate context and embeddings
        combined_input = tf.concat([expanded_context, embedded_input], axis=-1)
        return combined_input

    def _transform_gru_output(self, gru_output):
        """Transform GRU output to final predictions"""
        # Reshape for dense layer
        reshaped_output = tf.reshape(gru_output, (-1, gru_output.shape[2]))

        # Generate predictions
        predictions = self.output_projection(reshaped_output)
        return predictions

    def call(self, x, hidden, enc_output):
        """Main forward pass computation"""
        # Phase 1: Compute attention mechanism
        context_vector, attention_weights = self._compute_context_vector(hidden, enc_output)

        # Phase 2: Prepare decoder input
        decoder_input = self._prepare_input_sequence(x, context_vector)

        # Phase 3: Process through GRU
        gru_output, new_state = self.gru_cell(decoder_input)

        # Phase 4: Generate final output
        final_output = self._transform_gru_output(gru_output)

        return final_output, new_state, attention_weights


'''
LSTM Decoder Implementation - Refactored
'''
class LSTM_Decoder(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, dec_units, batch_sz, dropout=0):
        super(LSTM_Decoder, self).__init__()
        # Configuration storage
        self.batch_size = batch_sz
        self.decoder_units = dec_units
        self.vocab_length = vocab_size
        self.embedding_size = embedding_dim

        # Initialize all components in __init__
        self.token_embeddings = tf.keras.layers.Embedding(
            self.vocab_length,
            self.embedding_size
        )

        self.lstm_unit = tf.keras.layers.LSTM(
            self.decoder_units,
            return_sequences=True,
            return_state=True,
            recurrent_initializer='glorot_uniform',
            dropout=dropout
        )

        self.prediction_layer = tf.keras.layers.Dense(self.vocab_length)
        self.attention_mechanism = BahdanauAttention(self.decoder_units)

    def _extract_attention_context(self, hidden_state, encoder_sequence):
        """Compute attention context and weights"""
        attention_context, weights = self.attention_mechanism(hidden_state, encoder_sequence)
        return attention_context, weights

    def _combine_context_with_input(self, input_sequence, attention_context):
        """Combine attention context with input embeddings"""
        # Transform input to embeddings
        embedded_tokens = self.token_embeddings(input_sequence)

        # Prepare context for concatenation
        reshaped_context = tf.expand_dims(attention_context, 1)

        # Merge information streams
        merged_input = tf.concat([reshaped_context, embedded_tokens], axis=-1)
        return merged_input

    def _process_lstm_forward(self, lstm_input, hidden_state, cell_state):
        """Execute LSTM forward computation"""
        initial_states = [hidden_state, cell_state]
        lstm_out, final_hidden, final_cell = self.lstm_unit(lstm_input, initial_state=initial_states)
        return lstm_out, final_hidden, final_cell

    def _create_vocabulary_predictions(self, lstm_output):
        """Convert LSTM output to vocabulary predictions"""
        # Reshape output for dense layer
        reshaped_out = tf.reshape(lstm_output, (-1, lstm_output.shape[2]))

        # Generate predictions
        vocab_predictions = self.prediction_layer(reshaped_out)
        return vocab_predictions

    def call(self, x, hidden, enc_output, cell_state):
        """Execute complete LSTM decoder forward pass"""
        # Stage 1: Attention computation
        context_vector, attention_weights = self._extract_attention_context(hidden, enc_output)

        # Stage 2: Input preparation
        combined_input = self._combine_context_with_input(x, context_vector)

        # Stage 3: LSTM processing
        lstm_output, new_hidden, new_cell = self._process_lstm_forward(
            combined_input, hidden, cell_state
        )

        # Stage 4: Final prediction generation
        final_predictions = self._create_vocabulary_predictions(lstm_output)

        return final_predictions, [new_hidden, new_cell], attention_weights


'''
RNN Decoder Implementation - Refactored
'''
class RNN_Decoder(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, dec_units, batch_sz, dropout=0):
        super(RNN_Decoder, self).__init__()
        # Parameter storage
        self.batch_size = batch_sz
        self.hidden_units = dec_units
        self.vocabulary_count = vocab_size
        self.word_vector_dim = embedding_dim

        # Initialize all layers in __init__
        self.vocabulary_embeddings = tf.keras.layers.Embedding(
            input_dim=self.vocabulary_count,
            output_dim=self.word_vector_dim
        )

        self.simple_rnn = tf.keras.layers.SimpleRNN(
            units=self.hidden_units,
            return_sequences=True,
            return_state=True,
            recurrent_initializer='glorot_uniform',
            dropout=dropout
        )

        self.vocabulary_classifier = tf.keras.layers.Dense(units=self.vocabulary_count)
        self.attention_calculator = BahdanauAttention(self.hidden_units)

    def _get_attention_information(self, current_state, encoder_outputs):
        """Derive attention context and importance weights"""
        context_information, importance_weights = self.attention_calculator(
            current_state, encoder_outputs
        )
        return context_information, importance_weights

    def _convert_tokens_to_embeddings(self, token_sequence):
        """Convert token sequence to embedding vectors"""
        embedded_sequence = self.vocabulary_embeddings(token_sequence)
        return embedded_sequence

    def _merge_attention_and_embeddings(self, token_embeddings, attention_context):
        """Combine attention information with input embeddings"""
        # Reshape attention for concatenation
        attention_expanded = tf.expand_dims(attention_context, axis=1)

        # Concatenate information sources
        fused_representation = tf.concat([attention_expanded, token_embeddings], axis=-1)
        return fused_representation

    def _run_rnn_forward_pass(self, rnn_input):
        """Perform RNN forward pass computation"""
        sequence_output, final_state = self.simple_rnn(rnn_input)
        return sequence_output, final_state

    def _generate_vocabulary_scores(self, rnn_output):
        """Transform RNN output to vocabulary probability distribution"""
        # Flatten output for classification
        flattened_features = tf.reshape(rnn_output, (-1, rnn_output.shape[2]))

        # Compute vocabulary scores
        vocabulary_logits = self.vocabulary_classifier(flattened_features)
        return vocabulary_logits

    def call(self, x, hidden, enc_output):
        """Complete RNN decoder forward computation"""
        # Step 1: Attention mechanism computation
        attention_context, attention_weights = self._get_attention_information(hidden, enc_output)

        # Step 2: Input token processing
        token_embeddings = self._convert_tokens_to_embeddings(x)

        # Step 3: Information fusion
        decoder_input = self._merge_attention_and_embeddings(token_embeddings, attention_context)

        # Step 4: RNN processing
        rnn_output, final_state = self._run_rnn_forward_pass(decoder_input)

        # Step 5: Vocabulary prediction
        output_predictions = self._generate_vocabulary_scores(rnn_output)

        return output_predictions, final_state, attention_weights

'''
Fucntion - Calculating the loss function
Reference: https://stackoverflow.com/questions/62916592/loss-function-for-sequences-in-tensorflow-2-0
'''
def calculate_loss(real, pred):
  mask_position = tf.math.logical_not(tf.math.equal(real, 0))
  loss_value = loss_object(real, pred)

  mask_position = tf.cast(mask_position, dtype=loss_value.dtype)
  loss_value *= mask_position

  #returns the mean of the loss value
  return tf.reduce_mean(loss_value)



"""# Modular RNN Encoder-Decoder Model Builder for Sequence-to-Sequence Learning

This implements a flexible and modular approach to constructing encoder-decoder architectures using different types of recurrent neural networks (GRU, LSTM, or vanilla RNN). It provides both a concise and verbose method for building and testing these models, including separate functions to initialize, test, and display model configurations. The modular design allows for easy experimentation with various RNN types by simply changing the global `rnn_type` variable.

"""

def build_model(vocab_inp_size, vocab_tar_size, embedding_dim, units, BATCH_SIZE, dropout, train_input_batch):
    """
    Construct encoder-decoder architecture based on specified RNN type
    Refactored implementation with modular helper functions
    """
    # Phase 1: Initialize and test encoder component
    encoder_instance, encoder_states = _create_and_test_encoder(
        vocab_inp_size, embedding_dim, units, BATCH_SIZE, dropout, train_input_batch
    )

    # Phase 2: Initialize and test decoder component
    decoder_instance = _create_and_test_decoder(
        vocab_tar_size, embedding_dim, units, BATCH_SIZE, dropout, encoder_states
    )

    return encoder_instance, decoder_instance


def _create_and_test_encoder(input_vocab_size, embed_dim, hidden_units, batch_sz, dropout_rate, input_batch):
    """
    Factory function to create appropriate encoder based on RNN type
    """
    # Step 1: Determine encoder architecture
    encoder_model = _instantiate_encoder_architecture(
        input_vocab_size, embed_dim, hidden_units, batch_sz, dropout_rate
    )

    # Step 2: Initialize encoder states
    initial_states = _initialize_encoder_states(encoder_model)

    # Step 3: Perform forward pass test
    encoder_output, final_states = _execute_encoder_forward_pass(
        encoder_model, input_batch, initial_states
    )

    # Step 4: Display encoder information
    _display_encoder_specifications(encoder_output, final_states)

    # Step 5: Package encoder states for decoder
    packaged_states = _package_encoder_states(final_states, encoder_output)

    return encoder_model, packaged_states


def _instantiate_encoder_architecture(vocab_size, embedding_size, num_units, batch_size, dropout_prob):
    """
    Create encoder instance based on global RNN type configuration
    """
    encoder_mapping = {
        'GRU': lambda: GRU_Encoder(vocab_size, embedding_size, num_units, batch_size, dropout_prob),
        'LSTM': lambda: LSTM_Encoder(vocab_size, embedding_size, num_units, batch_size, dropout_prob),
        'RNN': lambda: RNN_Encoder(vocab_size, embedding_size, num_units, batch_size, dropout_prob)
    }

    if rnn_type in encoder_mapping:
        encoder_instance = encoder_mapping[rnn_type]()
        return encoder_instance
    else:
        raise ValueError(f"Unsupported RNN type: {rnn_type}")


def _initialize_encoder_states(encoder_model):
    """
    Initialize hidden states for the encoder based on its type
    """
    if rnn_type == 'GRU':
        hidden_state = encoder_model.initialize_hidden_state()
        return {'hidden': hidden_state}
    elif rnn_type == 'LSTM':
        hidden_state, cell_state = encoder_model.initialize_hidden_state()
        return {'hidden': hidden_state, 'cell': cell_state}
    elif rnn_type == 'RNN':
        hidden_state = encoder_model.initialize_hidden_state()
        return {'hidden': hidden_state}


def _execute_encoder_forward_pass(encoder_model, input_sequence, state_dict):
    """
    Run forward pass through encoder with appropriate state handling
    """
    if rnn_type == 'GRU':
        output, final_hidden = encoder_model(input_sequence, state_dict['hidden'])
        return output, {'hidden': final_hidden, 'output': output}
    elif rnn_type == 'LSTM':
        output, final_hidden, final_cell = encoder_model(
            input_sequence, state_dict['hidden'], state_dict['cell']
        )
        return output, {'hidden': final_hidden, 'cell': final_cell, 'output': output}
    elif rnn_type == 'RNN':
        output, final_hidden = encoder_model(input_sequence, state_dict['hidden'])
        return output, {'hidden': final_hidden, 'output': output}


def _display_encoder_specifications(encoder_output, state_information):
    """
    Print encoder output dimensions and specifications
    """
    # Display encoder output shape
    output_shape_info = f'Encoder output shape: (batch size, sequence length, units) {encoder_output.shape}'
    print(output_shape_info)

    # Display hidden state shape
    hidden_shape_info = f'Encoder Hidden state shape: (batch size, units) {state_information["hidden"].shape}'
    print(hidden_shape_info)

    # Display additional state info for LSTM
    if rnn_type == 'LSTM' and 'cell' in state_information:
        cell_shape_info = f'Encoder Cell state shape: (batch size, units) {state_information["cell"].shape}'
        print(cell_shape_info)


def _package_encoder_states(final_states, encoder_output):
    """
    Package encoder states and outputs for decoder initialization
    """
    packaged_data = {
        'hidden_state': final_states['hidden'],
        'encoder_output': encoder_output,
        'rnn_architecture': rnn_type
    }

    # Add cell state for LSTM
    if rnn_type == 'LSTM' and 'cell' in final_states:
        packaged_data['cell_state'] = final_states['cell']

    return packaged_data


def _create_and_test_decoder(target_vocab_size, embed_dim, hidden_units, batch_sz, dropout_rate, encoder_states):
    """
    Factory function to create and test appropriate decoder
    """
    # Step 1: Create decoder architecture
    decoder_model = _instantiate_decoder_architecture(
        target_vocab_size, embed_dim, hidden_units, batch_sz, dropout_rate
    )

    # Step 2: Prepare test input for decoder
    test_decoder_input = _prepare_decoder_test_input(batch_sz)

    # Step 3: Execute decoder forward pass
    decoder_output = _execute_decoder_forward_pass(
        decoder_model, test_decoder_input, encoder_states
    )

    # Step 4: Display decoder specifications
    _display_decoder_specifications(decoder_output)

    return decoder_model


def _instantiate_decoder_architecture(vocab_size, embedding_size, num_units, batch_size, dropout_prob):
    """
    Create decoder instance based on RNN type
    """
    decoder_factory = {
        'GRU': GRU_Decoder,
        'LSTM': LSTM_Decoder,
        'RNN': RNN_Decoder
    }

    if rnn_type in decoder_factory:
        decoder_class = decoder_factory[rnn_type]
        decoder_instance = decoder_class(vocab_size, embedding_size, num_units, batch_size, dropout_prob)
        return decoder_instance
    else:
        raise ValueError(f"Unknown RNN type for decoder: {rnn_type}")


def _prepare_decoder_test_input(batch_size):
    """
    Generate random test input for decoder validation
    """
    # Create random uniform input tensor
    random_input_shape = (batch_size, 1)
    test_input = tf.random.uniform(random_input_shape)
    return test_input


def _execute_decoder_forward_pass(decoder_model, test_input, encoder_information):
    """
    Run decoder forward pass with appropriate state handling
    """
    hidden_state = encoder_information['hidden_state']
    encoder_output = encoder_information['encoder_output']
    architecture_type = encoder_information['rnn_architecture']

    if architecture_type == 'GRU':
        output, _, _ = decoder_model(test_input, hidden_state, encoder_output)
        return output
    elif architecture_type == 'LSTM':
        cell_state = encoder_information['cell_state']
        output, _, _ = decoder_model(test_input, hidden_state, encoder_output, cell_state)
        return output
    elif architecture_type == 'RNN':
        output, _, _ = decoder_model(test_input, hidden_state, encoder_output)
        return output


def _display_decoder_specifications(decoder_output_tensor):
    """
    Print decoder output shape and specifications
    """
    shape_description = f'Decoder output shape: (batch_size, vocab size) {decoder_output_tensor.shape}'
    print(shape_description)


# Alternative verbose implementation with manual loops
def build_model_verbose(vocab_inp_size, vocab_tar_size, embedding_dim, units, BATCH_SIZE, dropout, train_input_batch):
    """
    Alternative implementation with more verbose, step-by-step processing
    """
    # Initialize variables
    encoder_instance = None
    decoder_instance = None
    encoder_states = None

    # Manual encoder selection (newbie-style approach)
    available_rnn_types = ['GRU', 'LSTM', 'RNN']
    selected_type = None

    # Find matching RNN type
    for i in range(len(available_rnn_types)):
        current_type = available_rnn_types[i]
        if current_type == rnn_type:
            selected_type = current_type
            break

    # Create encoder based on selection
    if selected_type == 'GRU':
        encoder_instance = _build_gru_encoder_manually(vocab_inp_size, embedding_dim, units, BATCH_SIZE, dropout, train_input_batch)
    elif selected_type == 'LSTM':
        encoder_instance = _build_lstm_encoder_manually(vocab_inp_size, embedding_dim, units, BATCH_SIZE, dropout, train_input_batch)
    elif selected_type == 'RNN':
        encoder_instance = _build_rnn_encoder_manually(vocab_inp_size, embedding_dim, units, BATCH_SIZE, dropout, train_input_batch)

    # Extract encoder information
    encoder_model = encoder_instance['model']
    encoder_states = encoder_instance['states']

    # Create decoder with manual approach
    if selected_type == 'GRU':
        decoder_instance = _build_gru_decoder_manually(vocab_tar_size, embedding_dim, units, BATCH_SIZE, dropout, encoder_states)
    elif selected_type == 'LSTM':
        decoder_instance = _build_lstm_decoder_manually(vocab_tar_size, embedding_dim, units, BATCH_SIZE, dropout, encoder_states)
    elif selected_type == 'RNN':
        decoder_instance = _build_rnn_decoder_manually(vocab_tar_size, embedding_dim, units, BATCH_SIZE, dropout, encoder_states)

    return encoder_model, decoder_instance


def _build_gru_encoder_manually(vocab_size, embed_dim, units, batch_size, dropout, input_batch):
    """Manual GRU encoder construction"""
    encoder = GRU_Encoder(vocab_size, embed_dim, units, batch_size, dropout)
    hidden = encoder.initialize_hidden_state()
    output, final_hidden = encoder(input_batch, hidden)

    print(f'Encoder output shape: (batch size, sequence length, units) {output.shape}')
    print(f'Encoder Hidden state shape: (batch size, units) {final_hidden.shape}')

    return {'model': encoder, 'states': {'hidden': final_hidden, 'output': output}}


def _build_lstm_encoder_manually(vocab_size, embed_dim, units, batch_size, dropout, input_batch):
    """Manual LSTM encoder construction"""
    encoder = LSTM_Encoder(vocab_size, embed_dim, units, batch_size, dropout)
    hidden, cell = encoder.initialize_hidden_state()
    output, final_hidden, final_cell = encoder(input_batch, hidden, cell)

    print(f'Encoder output shape: (batch size, sequence length, units) {output.shape}')
    print(f'Encoder Hidden state shape: (batch size, units) {final_hidden.shape}')

    return {'model': encoder, 'states': {'hidden': final_hidden, 'cell': final_cell, 'output': output}}


def _build_rnn_encoder_manually(vocab_size, embed_dim, units, batch_size, dropout, input_batch):
    """Manual RNN encoder construction"""
    encoder = RNN_Encoder(vocab_size, embed_dim, units, batch_size, dropout)
    hidden = encoder.initialize_hidden_state()
    output, final_hidden = encoder(input_batch, hidden)

    print(f'Encoder output shape: (batch size, sequence length, units) {output.shape}')
    print(f'Encoder Hidden state shape: (batch size, units) {final_hidden.shape}')

    return {'model': encoder, 'states': {'hidden': final_hidden, 'output': output}}


def _build_gru_decoder_manually(vocab_size, embed_dim, units, batch_size, dropout, encoder_states):
    """Manual GRU decoder construction"""
    decoder = GRU_Decoder(vocab_size, embed_dim, units, batch_size, dropout)
    test_input = tf.random.uniform((batch_size, 1))
    output, _, _ = decoder(test_input, encoder_states['hidden'], encoder_states['output'])

    print(f'Decoder output shape: (batch_size, vocab size) {output.shape}')
    return decoder


def _build_lstm_decoder_manually(vocab_size, embed_dim, units, batch_size, dropout, encoder_states):
    """Manual LSTM decoder construction"""
    decoder = LSTM_Decoder(vocab_size, embed_dim, units, batch_size, dropout)
    test_input = tf.random.uniform((batch_size, 1))
    output, _, _ = decoder(test_input, encoder_states['hidden'], encoder_states['output'], encoder_states['cell'])

    print(f'Decoder output shape: (batch_size, vocab size) {output.shape}')
    return decoder


def _build_rnn_decoder_manually(vocab_size, embed_dim, units, batch_size, dropout, encoder_states):
    """Manual RNN decoder construction"""
    decoder = RNN_Decoder(vocab_size, embed_dim, units, batch_size, dropout)
    test_input = tf.random.uniform((batch_size, 1))
    output, _, _ = decoder(test_input, encoder_states['hidden'], encoder_states['output'])

    print(f'Decoder output shape: (batch_size, vocab size) {output.shape}')
    return decoder

"""# Training Loop for RNN-Based Seq2Seq Model with Modular Epoch and Batch Management

This function defines a structured multi-epoch training loop for sequence-to-sequence models using GRU, LSTM, or RNN architectures. It modularizes key training operations such as state initialization, batch training, checkpointing, and logging. This design promotes clarity, flexibility, and ease of maintenance while tracking loss progression across epochs.

"""

def train_epochs(EPOCHS, encoder, decoder, dataset, steps_per_epoch):
    """Main training loop for multiple epochs with refactored internal structure"""

    def get_initial_encoder_states():
        """Get initial encoder states based on RNN type"""
        if rnn_type == 'LSTM':
            hidden_state, cell_state = encoder.initialize_hidden_state()
            return [hidden_state, cell_state]
        else:  # GRU or RNN
            return encoder.initialize_hidden_state()

    def execute_batch_training(batch_data, encoder_states):
        """Execute training for a single batch"""
        input_data, target_data = batch_data
        return train_batch(input_data, target_data, encoder_states, encoder, decoder, rnn_type)

    def handle_batch_logging(epoch_num, batch_num, loss_value):
        """Handle periodic batch logging"""
        if batch_num % 100 == 0:
            print(f'Epoch {epoch_num+1} Batch {batch_num} Loss {loss_value.numpy():.4f}')

    def manage_checkpoint_saving(epoch_num):
        """Manage checkpoint saving at regular intervals"""
        if (epoch_num + 1) % 2 == 0:
            checkpoint.save(file_prefix=checkpoint_prefix)

    def finalize_epoch_results(epoch_num, total_loss_value, start_time):
        """Calculate and display epoch results"""
        average_loss = total_loss_value / steps_per_epoch
        time_elapsed = time.time() - start_time

        print(f'Epoch {epoch_num+1} Loss {average_loss:.4f}')
        print(f'Time taken for 1 epoch {time_elapsed:.2f} sec\n')

        return average_loss

    # Main training loop implementation
    loss_tracking = [0] * EPOCHS

    for epoch_index in range(EPOCHS):
        timer_start = time.time()

        # Set up encoder states for this epoch
        encoder_initial_states = get_initial_encoder_states()

        # Track cumulative loss for the epoch
        cumulative_loss = 0
        batch_index = 0

        # Iterate through dataset batches
        for batch_index, current_batch in enumerate(dataset.take(steps_per_epoch)):
            # Process current batch and get loss
            batch_loss_result = execute_batch_training(current_batch, encoder_initial_states)

            # Accumulate loss
            cumulative_loss += batch_loss_result

            # Log progress if needed
            handle_batch_logging(epoch_index, batch_index, batch_loss_result)

        # Handle epoch completion tasks
        manage_checkpoint_saving(epoch_index)

        # Calculate and log epoch summary
        epoch_avg_loss = finalize_epoch_results(epoch_index, cumulative_loss, timer_start)

        # Store the average loss for this epoch
        loss_tracking[epoch_index] = epoch_avg_loss.numpy()

    return loss_tracking

"""# Modular Seq2Seq Training Pipeline with Optional WandB Support

This pipeline orchestrates the full training process for RNN-based sequence-to-sequence models using TensorFlow.

### Core Functions:

- **Experiment Setup**: `_configure_wandb_experiment` initializes WandB or defaults hyperparameters.
- **Data Handling**: `_compute_dataset_metrics` and `_build_training_pipeline` prepare and batch the dataset.
- **Model Creation**: `_create_model_architecture` builds the encoder-decoder and sets up training components.
- **Checkpointing**: `_establish_checkpointing` manages model saving/restoration.
- **Training Loop**: `_run_training_epochs` runs training with logging and periodic checkpointing.
- **Evaluation**: `_evaluate_model_performance` validates and logs accuracy.
- **Execution**: `train` coordinates the full workflow.

Supports clean modularity, WandB logging, and easy hyperparameter tuning.

"""

def _configure_wandb_experiment(use_wandb=True):
    """Setup wandb configuration and extract hyperparameters"""
    if not use_wandb:
        # Return default values if wandb is not used
        return None, {
            'rnn_architecture': 'GRU',
            'batch_dimension': 64,
            'embedding_size': 256,
            'hidden_units': 1024,
            'training_epochs': 10,
            'dropout_rate': 0.1
        }

    experiment_run = wandb.init()
    hyperparameter_config = {
        'rnn_architecture': experiment_run.config.rnn_type,
        'batch_dimension': experiment_run.config.bs,
        'embedding_size': experiment_run.config.embed,
        'hidden_units': experiment_run.config.latent,
        'training_epochs': experiment_run.config.epochs,
        'dropout_rate': experiment_run.config.dropout
    }

    print("Selected RNN Architecture:", hyperparameter_config['rnn_architecture'])
    return experiment_run, hyperparameter_config

def _compute_dataset_metrics():
    """Calculate dataset dimensions and vocabulary parameters"""
    dataset_buffer_size = len(input_tensor_train)
    epoch_steps = len(input_tensor_train) // BATCH_SIZE
    input_vocab_dimension = len(inp_lang.word_index) + 1
    target_vocab_dimension = len(targ_lang.word_index) + 1

    return {
        'buffer_size': dataset_buffer_size,
        'steps_per_epoch': epoch_steps,
        'vocab_inp_size': input_vocab_dimension,
        'vocab_tar_size': target_vocab_dimension
    }

def _create_experiment_name(config_dict, use_wandb):
    """Generate unique experiment identifier from hyperparameters"""
    name_components = [
        f"_epochs_{config_dict['training_epochs']}",
        f"_rnn_type_{config_dict['rnn_architecture']}",
        f"_bs_{config_dict['batch_dimension']}",
        f"_embed_{config_dict['embedding_size']}",
        f"_latent_{config_dict['hidden_units']}",
        f"_dropout_{config_dict['dropout_rate']}"
    ]

    experiment_name = ''.join(name_components)

    if use_wandb:
        wandb.run.name = experiment_name

    return experiment_name

def _build_training_pipeline():
    """Create and configure the training data pipeline"""
    dataset_metrics = _compute_dataset_metrics()

    # Build tensor dataset with shuffling
    data_pipeline = tf.data.Dataset.from_tensor_slices(
        (input_tensor_train, target_tensor_train)
    ).shuffle(dataset_metrics['buffer_size'])

    # Apply batching with remainder dropping
    batched_pipeline = data_pipeline.batch(BATCH_SIZE, drop_remainder=True)

    # Get sample for model initialization
    sample_input_batch, sample_target_batch = next(iter(batched_pipeline))

    return batched_pipeline, sample_input_batch, sample_target_batch, dataset_metrics

def _create_model_architecture(vocab_metrics, hyperparams, sample_data):
    """Build encoder-decoder model and training components"""
    # Create model components
    encoder_net, decoder_net = build_model(
        vocab_metrics['vocab_inp_size'],
        vocab_metrics['vocab_tar_size'],
        hyperparams['embedding_size'],
        hyperparams['hidden_units'],
        hyperparams['batch_dimension'],
        hyperparams['dropout_rate'],
        sample_data
    )

    # Initialize training components
    training_optimizer = tf.keras.optimizers.Adam()
    loss_function = tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True, reduction='none'
    )

    return encoder_net, decoder_net, training_optimizer, loss_function

def _establish_checkpointing(encoder_net, decoder_net, training_optimizer):
    """Setup model checkpointing infrastructure"""
    checkpoint_storage_dir = os.path.join(os.getcwd(), 'training_checkpoints')
    checkpoint_path_prefix = os.path.join(checkpoint_storage_dir, "ckpt")

    checkpoint_handler = tf.train.Checkpoint(
        optimizer=training_optimizer,
        encoder=encoder_net,
        decoder=decoder_net
    )

    return checkpoint_handler, checkpoint_path_prefix

def _run_training_epochs(hyperparams, data_pipeline, dataset_metrics,
                        encoder_net, decoder_net, use_wandb):
    """Execute the complete training process across all epochs"""
    epoch_losses = [0] * hyperparams['training_epochs']
    architecture_type = hyperparams['rnn_architecture']

    for current_epoch in range(hyperparams['training_epochs']):
        epoch_timer = time.time()

        # Setup encoder initial states
        if architecture_type != 'LSTM':
            initial_hidden = encoder_net.initialize_hidden_state()
            encoder_states = initial_hidden
        else:
            hidden_state, cell_state = encoder_net.initialize_hidden_state()
            encoder_states = [hidden_state, cell_state]

        # Process epoch batches
        accumulated_loss = 0
        final_batch_idx = 0

        for final_batch_idx, (batch_input, batch_target) in enumerate(
            data_pipeline.take(dataset_metrics['steps_per_epoch'])
        ):
            # Train single batch
            batch_loss_value = train_batch(
                batch_input, batch_target, encoder_states,
                encoder_net, decoder_net, architecture_type
            )
            accumulated_loss += batch_loss_value

        # Periodic batch logging
        if final_batch_idx % 100 == 0:
            print(f'Epoch {current_epoch+1} Batch {final_batch_idx} '
                  f'Loss {batch_loss_value.numpy():.4f}')

        # Checkpoint saving
        if (current_epoch + 1) % 2 == 0:
            checkpoint.save(file_prefix=checkpoint_prefix)

        # Epoch summary
        mean_epoch_loss = accumulated_loss / dataset_metrics['steps_per_epoch']
        elapsed_time = time.time() - epoch_timer

        print(f'Epoch {current_epoch+1} Loss {mean_epoch_loss:.4f}')
        print(f'Time taken for 1 epoch {elapsed_time:.2f} sec\n')

        # Store and log results
        epoch_losses[current_epoch] = mean_epoch_loss.numpy()
        if use_wandb:
            wandb.log({"train_loss": mean_epoch_loss.numpy()})

    return epoch_losses

def _evaluate_model_performance(experiment_id, architecture_type, use_wandb):
    """Perform model validation and metric logging"""
    model_accuracy = validate(vaildation_file_path, architecture_type)

    print("Model Validation Accuracy:", model_accuracy)

    if use_wandb:
        wandb.log({'val_accuracy': model_accuracy})

    return model_accuracy

def _load_final_checkpoint():
    """Restore the most recent model checkpoint"""
    most_recent_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
    if most_recent_checkpoint:
        checkpoint.restore(most_recent_checkpoint)

def train(use_wandb=True):
    """Refactored main training orchestration function"""
    # Global variable declarations
    global BATCH_SIZE, units, vocab_inp_size, vocab_tar_size
    global embedding_dim, encoder, decoder, optimizer, loss_object
    global checkpoint_dir, checkpoint_prefix, checkpoint, run_name, rnn_type

    # Phase 1: Experiment configuration
    wandb_session, config_parameters = _configure_wandb_experiment(use_wandb)

    # Phase 2: Global parameter assignment
    rnn_type = config_parameters['rnn_architecture']
    BATCH_SIZE = config_parameters['batch_dimension']
    embedding_dim = config_parameters['embedding_size']
    units = config_parameters['hidden_units']
    EPOCHS = config_parameters['training_epochs']
    dropout = config_parameters['dropout_rate']

    # Phase 3: Dataset preparation
    training_data, sample_inp, sample_targ, data_metrics = _build_training_pipeline()

    # Phase 4: Global vocabulary assignment
    vocab_inp_size = data_metrics['vocab_inp_size']
    vocab_tar_size = data_metrics['vocab_tar_size']

    # Phase 5: Experiment naming
    run_name = _create_experiment_name(config_parameters, use_wandb)

    # Phase 6: Model and optimizer creation
    encoder, decoder, optimizer, loss_object = _create_model_architecture(
        data_metrics, config_parameters, sample_inp
    )

    # Phase 7: Checkpoint system setup
    checkpoint, checkpoint_prefix = _establish_checkpointing(encoder, decoder, optimizer)
    checkpoint_dir = os.path.dirname(checkpoint_prefix)

    # Phase 8: Main training execution
    loss_progression = _run_training_epochs(
        config_parameters, training_data, data_metrics, encoder, decoder, use_wandb
    )

    # Phase 9: Model evaluation
    final_accuracy = _evaluate_model_performance(run_name, rnn_type, use_wandb)

    # Phase 10: Results summary
    print("Complete Training Loss History:", loss_progression)
    print("Final Model Validation Score:", final_accuracy)

    # Phase 11: Checkpoint restoration
    _load_final_checkpoint()

    return loss_progression, final_accuracy

def configure_model_parameters():
    """
    Initialize and return the optimal hyperparameters for model training
    """
    config = {
        'rnn_architecture': 'LSTM',
        'batch_size': 64,
        'embedding_dimensions': 512,
        'hidden_units': 1024,
        'training_epochs': 20,
        'dropout_rate': 0.2
    }

    print(f"RNN Architecture: {config['rnn_architecture']}")
    return config

def calculate_training_metrics(config):
    """
    Calculate buffer size, steps per epoch, and vocabulary sizes
    """
    buffer_size = len(input_tensor_train)
    steps_per_epoch = len(input_tensor_train) // config['batch_size']
    input_vocab_size = len(inp_lang.word_index) + 1
    target_vocab_size = len(targ_lang.word_index) + 1

    return buffer_size, steps_per_epoch, input_vocab_size, target_vocab_size

def generate_run_identifier(config):
    """
    Create a unique identifier for the current training run
    """
    identifier = (f"_epochs_{config['training_epochs']}"
                 f"_rnn_type_{config['rnn_architecture']}"
                 f"_bs_{config['batch_size']}"
                 f"_embed_{config['embedding_dimensions']}"
                 f"_latent_{config['hidden_units']}"
                 f"_dropout_{config['dropout_rate']}")
    return identifier

def prepare_training_dataset(config, buffer_size):
    """
    Create and configure the training dataset with batching
    """
    dataset = tf.data.Dataset.from_tensor_slices(
        (input_tensor_train, target_tensor_train)
    ).shuffle(buffer_size)

    # Create batches and drop incomplete final batch for consistent training
    dataset = dataset.batch(config['batch_size'], drop_remainder=True)

    # Extract sample batch for model initialization
    sample_input, sample_target = next(iter(dataset))

    return dataset, sample_input, sample_target

def initialize_model_components(config, input_vocab_size, target_vocab_size, sample_input):
    """
    Build encoder-decoder architecture and initialize training components
    """
    # Construct the neural network architecture
    encoder_model, decoder_model = build_model(
        input_vocab_size,
        target_vocab_size,
        config['embedding_dimensions'],
        config['hidden_units'],
        config['batch_size'],
        config['dropout_rate'],
        sample_input
    )

    # Initialize loss computation
    sparse_categorical_loss = tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True, reduction='none'
    )

    return encoder_model, decoder_model, sparse_categorical_loss

def setup_optimizer_and_checkpoint(encoder_model, decoder_model):
    """
    Initialize optimizer and configure checkpoint system
    """
    # Create optimizer outside of any tf.function context
    adam_optimizer = tf.keras.optimizers.Adam()

    # Build optimizer state by running a dummy forward pass
    # This ensures the optimizer variables are created properly
    dummy_gradients = []
    trainable_vars = encoder_model.trainable_variables + decoder_model.trainable_variables

    for var in trainable_vars:
        dummy_gradients.append(tf.zeros_like(var))

    # Initialize optimizer state
    adam_optimizer.apply_gradients(zip(dummy_gradients, trainable_vars))

    # Setup checkpoint system
    checkpoint_directory = os.path.join(os.getcwd(), 'training_checkpoints')
    checkpoint_file_prefix = os.path.join(checkpoint_directory, "ckpt")

    checkpoint_manager = tf.train.Checkpoint(
        optimizer=adam_optimizer,
        encoder=encoder_model,
        decoder=decoder_model
    )

    return adam_optimizer, checkpoint_directory, checkpoint_file_prefix, checkpoint_manager

def execute_training_process(config, encoder_model, decoder_model, dataset, steps_per_epoch):
    """
    Run the complete training loop for specified epochs
    """
    training_losses = [0] * config['training_epochs']

    # Execute the training procedure
    training_losses = train_epochs(
        config['training_epochs'],
        encoder_model,
        decoder_model,
        dataset,
        steps_per_epoch
    )

    return training_losses

def evaluate_model_performance(run_identifier, rnn_architecture):
    """
    Assess model performance on validation and test datasets
    """
    test_performance = validate(test_file_path, run_identifier)
    validation_performance = validate(vaildation_file_path, rnn_architecture)

    return test_performance, validation_performance

def restore_and_generate_outputs(checkpoint_manager, checkpoint_directory, rnn_architecture, run_identifier):
    """
    Restore best model and generate sample outputs and connectivity analysis
    """
    # Load the most recent checkpoint
    checkpoint_manager.restore(tf.train.latest_checkpoint(checkpoint_directory))

    # Generate sample inputs using the trained model
    generate_inputs(rnn_architecture, 10)

    # Analyze model connectivity with predefined test cases
    test_words = ['maryaadaa', 'prayogshala', 'angarakshak']
    output_directory = os.path.join(os.getcwd(), "predictions_attention", str(run_identifier))
    connectivity(test_words, rnn_architecture, output_directory)

def manual_train():
    """
    Orchestrate the complete manual training process with optimal configuration
    """
    # Set global variables for compatibility
    global BATCH_SIZE, units, vocab_inp_size, vocab_tar_size, embedding_dim
    global encoder, decoder, optimizer, loss_object
    global checkpoint_dir, checkpoint_prefix, checkpoint, run_name, rnn_type

    # Step 1: Configure hyperparameters
    config = configure_model_parameters()

    # Step 2: Calculate training metrics
    buffer_size, steps_per_epoch, input_vocab_size, target_vocab_size = calculate_training_metrics(config)

    # Step 3: Generate run identifier
    run_identifier = generate_run_identifier(config)

    # Step 4: Prepare dataset
    dataset, sample_input, sample_target = prepare_training_dataset(config, buffer_size)

    # Step 5: Initialize model components
    encoder_model, decoder_model, sparse_categorical_loss = initialize_model_components(
        config, input_vocab_size, target_vocab_size, sample_input
    )

    # Step 6: Setup optimizer and checkpoint system
    adam_optimizer, checkpoint_directory, checkpoint_file_prefix, checkpoint_manager = setup_optimizer_and_checkpoint(
        encoder_model, decoder_model
    )

    # Step 7: Execute training
    training_losses = execute_training_process(config, encoder_model, decoder_model, dataset, steps_per_epoch)

    # Step 8: Evaluate performance
    test_performance, validation_performance = evaluate_model_performance(run_identifier, config['rnn_architecture'])

    # Step 9: Display results
    print(f"Training losses: {training_losses}")
    print(f"Validation Accuracy: {validation_performance}")
    print(f"Test Accuracy: {test_performance}")

    # Step 10: Generate outputs and analysis
    restore_and_generate_outputs(checkpoint_manager, checkpoint_directory, config['rnn_architecture'], run_identifier)

    # Update global variables for backward compatibility
    BATCH_SIZE = config['batch_size']
    units = config['hidden_units']
    vocab_inp_size = input_vocab_size
    vocab_tar_size = target_vocab_size
    embedding_dim = config['embedding_dimensions']
    encoder = encoder_model
    decoder = decoder_model
    optimizer = adam_optimizer
    loss_object = sparse_categorical_loss
    checkpoint_dir = checkpoint_directory
    checkpoint_prefix = checkpoint_file_prefix
    checkpoint = checkpoint_manager
    run_name = run_identifier
    rnn_type = config['rnn_architecture']

"""# Training Batch Execution (Seq2Seq)

These functions define the core logic for processing one training batch using teacher forcing.

### Core Functions:

- **`initialize_encoder_states`**:
  - Feeds input to the encoder and returns hidden (and cell) states based on RNN type (LSTM, GRU, or RNN).

- **`prepare_decoder_initial_input`**:
  - Initializes decoder input with start-of-sequence tokens.

- **`execute_decoder_step`**:
  - Runs a single step of the decoder; handles LSTM-specific state passing logic.

- **`compute_sequence_loss`**:
  - Iterates over target sequence and computes cumulative loss using teacher forcing.

- **`perform_gradient_update`**:
  - Computes gradients and updates model parameters (not used directly in current flow).

### Training Loop:

- **`train_batch`** (`@tf.function`-decorated):
  - Encodes input, prepares initial decoder input, computes sequence loss,
    calculates gradients, and updates parameters using optimizer.
  - Returns average loss per token for the batch.

"""

def initialize_encoder_states(input_data, hidden_state, encoder_model, architecture_type):
    """
    Process input through encoder and return appropriate states based on RNN architecture
    """
    if architecture_type == 'LSTM':
        # LSTM returns output, hidden state, and cell state
        encoder_output, hidden_state, cell_state = encoder_model(
            input_data, hidden_state[0], hidden_state[1]
        )
        return encoder_output, hidden_state, cell_state
    else:
        # GRU and vanilla RNN return output and hidden state only
        encoder_output, hidden_state = encoder_model(input_data, hidden_state)
        return encoder_output, hidden_state, None

def prepare_decoder_initial_input(batch_size, target_tokenizer):
    """
    Create the initial decoder input using start-of-sequence tokens
    """
    start_token_id = target_tokenizer.word_index['\t']
    initial_decoder_input = tf.expand_dims([start_token_id] * batch_size, 1)
    return initial_decoder_input

def execute_decoder_step(decoder_input, decoder_hidden_state, encoder_output,
                        decoder_model, architecture_type, step_number, cell_state=None):
    """
    Execute a single decoder step with appropriate state handling for different RNN types
    """
    if architecture_type == 'LSTM':
        if step_number == 1:
            # First LSTM step uses both hidden and cell states
            predictions, new_hidden_state, attention_weights = decoder_model(
                decoder_input, decoder_hidden_state, encoder_output, cell_state
            )
        else:
            # Subsequent LSTM steps extract hidden state from tuple
            predictions, new_hidden_state, attention_weights = decoder_model(
                decoder_input, decoder_hidden_state[0], encoder_output, cell_state
            )
    else:
        # GRU and vanilla RNN processing
        predictions, new_hidden_state, attention_weights = decoder_model(
            decoder_input, decoder_hidden_state, encoder_output
        )

    return predictions, new_hidden_state, attention_weights

def compute_sequence_loss(target_sequence, decoder_model, decoder_input,
                         decoder_hidden, encoder_output, architecture_type, cell_state=None):
    """
    Calculate cumulative loss across the entire target sequence using teacher forcing
    """
    cumulative_loss = 0
    sequence_length = target_sequence.shape[1]

    # Iterate through each time step in the sequence
    for time_step in range(1, sequence_length):
        # Get predictions for current time step
        predictions, decoder_hidden, _ = execute_decoder_step(
            decoder_input, decoder_hidden, encoder_output,
            decoder_model, architecture_type, time_step, cell_state
        )

        # Accumulate loss for current prediction
        step_loss = calculate_loss(target_sequence[:, time_step], predictions)
        cumulative_loss += step_loss

        # Apply teacher forcing: use ground truth as next input
        decoder_input = tf.expand_dims(target_sequence[:, time_step], 1)

    return cumulative_loss

def perform_gradient_update(total_loss, encoder_model, decoder_model, optimizer_instance):
    """
    Calculate gradients and apply parameter updates
    """
    # Collect all trainable parameters from both models
    trainable_parameters = encoder_model.trainable_variables + decoder_model.trainable_variables

    # Compute gradients with respect to total loss
    parameter_gradients = tf.gradients(total_loss, trainable_parameters)

    # Apply gradient-based parameter updates
    optimizer_instance.apply_gradients(zip(parameter_gradients, trainable_parameters))

@tf.function
def train_batch(inp, targ, enc_hidden, encoder, decoder, rnn_type):
    """
    Execute training for a single batch and return normalized batch loss
    """
    # Initialize total loss accumulator
    total_sequence_loss = 0

    # Use gradient tape to track operations for backpropagation
    with tf.GradientTape() as gradient_tracker:
        # Process input through encoder based on architecture type
        encoder_output, decoder_hidden, cell_state = initialize_encoder_states(
            inp, enc_hidden, encoder, rnn_type
        )

        # Prepare initial decoder input with start tokens
        decoder_input = prepare_decoder_initial_input(BATCH_SIZE, targ_lang)

        # Compute loss across entire sequence
        total_sequence_loss = compute_sequence_loss(
            targ, decoder, decoder_input, decoder_hidden,
            encoder_output, rnn_type, cell_state
        )

    # Calculate normalized batch loss
    normalized_batch_loss = total_sequence_loss / int(targ.shape[1])

    # Collect trainable variables from both models
    model_variables = encoder.trainable_variables + decoder.trainable_variables

    # Compute gradients of loss with respect to model parameters
    loss_gradients = gradient_tracker.gradient(total_sequence_loss, model_variables)

    # Apply computed gradients to update model parameters
    optimizer.apply_gradients(zip(loss_gradients, model_variables))

    return normalized_batch_loss

"""#Inference Model Function
This function generates the predicted output word from a given input word using a trained sequence-to-sequence model with attention. It handles input preprocessing, runs the encoder, and then uses the decoder iteratively to produce characters while collecting attention weights, stopping when the end-of-sequence token is predicted.
"""

'''
Function - inference_model
generating the predicted word, input word, attention weights and the attention plot
'''
def inference_model(input_word,rnn_type):
  #creating an empty attention plot
  attention_plot = np.zeros((max_length_targ, max_length_inp))

  #preprocessing the input word
  input_word = word_process(input_word)

  #converting the word to tensor after pading
  inputs = [inp_lang.word_index[i] for i in input_word]
  inputs = tf.keras.preprocessing.sequence.pad_sequences([inputs], maxlen=max_length_inp, padding='post')
  inputs = tf.convert_to_tensor(inputs)

  #predicted word initialization
  predicted_word = ''

  #if cell type is GRU or RNN
  if rnn_type!='LSTM':
    hidden = [tf.zeros((1, units))]
    enc_out, enc_hidden = encoder(inputs, hidden)
    dec_hidden = enc_hidden
  #if cell type is LSTM
  elif rnn_type=='LSTM':
    hidden=tf.zeros((1, units))
    cell_state= tf.zeros((1, units))
    enc_out, enc_hidden,enc_cell_state = encoder(inputs, hidden,cell_state)
    dec_hidden = enc_hidden

  #generating the decode inputs
  dec_input = tf.expand_dims([targ_lang.word_index['\t']], 0)

  #storing the attention weights
  att_w=[]

  #calculating the predictions
  for t in range(max_length_targ):
    #if cell is GRU or RNN
    if rnn_type!='LSTM':
      predictions, dec_hidden, attention_weights = decoder(dec_input,dec_hidden,enc_out)
    #if cell is LSTM
    elif rnn_type=='LSTM':
      predictions, dec_hidden, attention_weights = decoder(dec_input, dec_hidden, enc_out, enc_cell_state)
      dec_hidden=dec_hidden[0]

    # storing the attention weights for plotting latter
    attention_weights = tf.reshape(attention_weights, (-1, ))
    attention_plot[t] = attention_weights.numpy()
    att_w.append(attention_weights.numpy()[0:len(input_word)])


    #predicted id
    predicted_id = tf.argmax(predictions[0]).numpy()
    #predicted word
    predicted_word += targ_lang.index_word[predicted_id]

    #in case of last character
    if targ_lang.index_word[predicted_id] == '\n':
      return predicted_word, input_word, attention_plot,att_w

    # the predicted ID is fed back into the model
    dec_input = tf.expand_dims([predicted_id], 0)
  #finally return the predicted word, input word, attention plot and the attention weight
  return predicted_word, input_word, attention_plot,att_w

"""#Validation Function
This function evaluates the model's prediction accuracy on a dataset by comparing predicted outputs to target sequences. It supports saving predictions into success and failure files when validating test data, and returns the overall accuracy of predictions.
"""

def _setup_prediction_directories(file_path, folder_name):
    """Helper function to create directory structure for test predictions"""
    predictions_dir = os.path.join(os.getcwd(), "predictions_attention")
    target_folder = os.path.join(predictions_dir, str(folder_name))

    # Clean existing folder if it exists
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)

    # Create directory structure
    if not os.path.exists(predictions_dir):
        os.mkdir(predictions_dir)
    os.mkdir(target_folder)

    return target_folder

def _initialize_output_files(folder_path):
    """Helper function to create and open output files for predictions"""
    success_filepath = os.path.join(folder_path, "success.txt")
    failure_filepath = os.path.join(folder_path, "failure.txt")

    success_handle = open(success_filepath, "w", encoding='utf-8', errors='ignore')
    failure_handle = open(failure_filepath, "w", encoding='utf-8', errors='ignore')

    return success_handle, failure_handle

def _process_single_prediction(input_text, target_text, rnn_model_type):
    """Helper function to generate prediction for a single input"""
    predicted_text, processed_input, attention_data, attention_weights = inference_model(input_text, rnn_model_type)

    # Format record for output
    formatted_record = f"{processed_input.strip()} {target_text.strip()} {predicted_text[:-1].strip()}\n"

    return predicted_text, formatted_record

def _evaluate_prediction_accuracy(target_text, predicted_text):
    """Helper function to check if prediction matches target"""
    # Handle formatting differences (target has leading tab, both have trailing newline)
    normalized_target = target_text[1:]  # Remove leading tab
    return normalized_target == predicted_text

def _write_prediction_result(record, is_correct, success_file, failure_file):
    """Helper function to write prediction results to appropriate file"""
    if is_correct and success_file:
        success_file.write(record)
    elif not is_correct and failure_file:
        failure_file.write(record)

def _cleanup_files(file_handles):
    """Helper function to safely close file handles"""
    for handle in file_handles:
        if handle:
            handle.close()

def validate(path_to_file, folder_name):
    """
    Main validation function that computes accuracy on validation/test data
    and optionally saves prediction results to files
    """
    # Determine if we need to save predictions based on file path
    should_save_predictions = "test" in path_to_file
    success_file_handle = None
    failure_file_handle = None

    # Setup output directories and files if needed
    if should_save_predictions:
        output_folder = _setup_prediction_directories(path_to_file, folder_name)
        success_file_handle, failure_file_handle = _initialize_output_files(output_folder)

    # Load dataset for evaluation
    target_sequences, input_sequences = create_dataset(path_to_file)

    # Initialize accuracy counter
    correct_predictions = 0
    total_samples = len(input_sequences)

    # Process each input-target pair
    for idx in range(total_samples):
        current_input = input_sequences[idx]
        current_target = target_sequences[idx]

        # Generate prediction
        prediction_result, output_record = _process_single_prediction(
            current_input, current_target, rnn_type
        )

        # Check accuracy
        is_prediction_correct = _evaluate_prediction_accuracy(current_target, prediction_result)

        # Update counter
        if is_prediction_correct:
            correct_predictions += 1

        # Save results if required
        if should_save_predictions:
            _write_prediction_result(
                output_record, is_prediction_correct,
                success_file_handle, failure_file_handle
            )

    # Cleanup resources
    if should_save_predictions:
        _cleanup_files([success_file_handle, failure_file_handle])

    # Calculate and return accuracy
    accuracy_score = correct_predictions / total_samples
    return accuracy_score

"""#Attention Plotting Function
This function visualizes the attention weights between input and predicted words using a heatmap. It sets up labels with Hindi font support and saves the plot, aiding in interpreting which input characters the model focused on during each decoding step.
"""

def plot_attention(attention, input_word, predicted_word, file_name):
    # Set up the font for displaying Hindi characters
    hindi_font_path = os.path.join(os.getcwd(), "Nirmala.ttf")
    hindi_font = FontProperties(fname=hindi_font_path)

    # Create a figure for the heatmap
    fig = plt.figure(figsize=(3, 3))
    ax = fig.add_subplot(1, 1, 1)

    # Show attention matrix
    ax.matshow(attention, cmap='viridis')

    # Set tick labels
    _set_axis_labels(ax, input_word, predicted_word, hindi_font)

    # Save and display the attention plot
    plt.tight_layout()
    plt.savefig(file_name)
    plt.show()



def _set_axis_labels(ax, input_text, output_text, font):
    font_opts = {'fontsize': 14}

    # Set x-axis labels
    x_labels = ['']
    for ch in input_text:
        x_labels.append(ch)
    ax.set_xticklabels(x_labels, fontdict=font_opts)

    # Set y-axis labels with Hindi font
    y_labels = ['']
    for ch in output_text:
        y_labels.append(ch)
    ax.set_yticklabels(y_labels, fontdict=font_opts, fontproperties=font)

    # Set tick interval to 1 for clarity
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

"""
Geting the connectivity html file.
"""

def cstr(s, color='black'):
    """
    Create HTML text element with background color styling.

    Args:
        s: Text content to style
        color: Background color for the text

    Returns:
        HTML formatted string with styling
    """
    if s.strip() == '':
        # Handle whitespace characters with special padding
        return f'<span style="color:#000000;padding-left:10px;background-color:{color};">&nbsp;</span>'
    else:
        # Regular text with background color
        return f'<span style="color:#000000;background-color:{color};">{s}&nbsp;</span>'


def print_color(t):
    """
    Display colored HTML text from tuples of (text, color) pairs.

    Args:
        t: List of tuples containing (text, color) pairs
    """
    # Combine all HTML elements into single string
    html_content = ''.join([cstr(text_item, color=color_item) for text_item, color_item in t])

    # Display the HTML (assumes display and html_print are available in environment)
    display(html_print(html_content))


def get_clr(value):
    """
    Map attention weight values to appropriate background colors.
    Uses gradient from blue (low attention) to red (high attention).

    Args:
        value: Attention weight value (expected range 0-1)

    Returns:
        Hex color code string
    """
    # Color palette: blue tones for low values, red tones for high values
    color_palette = [
        '#85c2e1', '#89c4e2', '#95cae5', '#99cce6', '#a1d0e8',
        '#b2d9ec', '#baddee', '#c2e1f0', '#eff7fb', '#f9e8e8',
        '#f9e8e8', '#f9d4d4', '#f9bdbd', '#f8a8a8', '#f68f8f',
        '#f47676', '#f45f5f', '#f34343', '#f33b3b', '#f42e2e'
    ]

    # Scale value to color index (0-19)
    color_index = min(int((value * 100) / 5), len(color_palette) - 1)
    return color_palette[color_index]


def visualize(input_word, output_word, att_w):
    """
    Create visualization of attention weights between input and output sequences.

    Args:
        input_word: List of input tokens/characters
        output_word: List of output tokens/characters
        att_w: 2D array of attention weights [output_len x input_len]
    """
    # Process each output character
    for output_idx in range(len(output_word)):
        print(f"\nOutput character: {output_word[output_idx]}\n")

        # Create color-coded representation for current output character
        colored_tokens = []

        # Map each input character to its attention weight color
        for input_idx in range(len(att_w[output_idx])):
            attention_weight = att_w[output_idx][input_idx]
            background_color = get_clr(attention_weight)

            # Create tuple of (character, color) for visualization
            token_color_pair = (input_word[input_idx], background_color)
            colored_tokens.append(token_color_pair)

        # Display the colored sequence
        print_color(colored_tokens)

"""
Code for connectivity visualisation.
"""
import os

def get_shade_color(value):
    """
    Convert attention weight value to corresponding green shade color.
    Higher values get darker green colors to indicate stronger connections.

    Args:
        value: Attention weight value (0-1 range)

    Returns:
        Hex color code string representing green shade
    """
    # Green gradient palette from light to dark
    green_shades = [
        '#00fa00', '#00f500', '#00eb00', '#00e000', '#00db00',
        '#00d100', '#00c700', '#00c200', '#00b800', '#00ad00',
        '#00a800', '#009e00', '#009400', '#008f00', '#008500',
        '#007500', '#007000', '#006600', '#006100', '#005c00',
        '#005200', '#004d00', '#004700', '#003d00', '#003800',
        '#003300', '#002900', '#002400', '#001f00', '#001400'
    ]

    # Map value to color index
    shade_index = min(int((value * 100) / 5), len(green_shades) - 1)
    return green_shades[shade_index]


def create_file(text_colors, input_word, output_word, file_path=None):
    """
    Generate interactive HTML file for connectivity visualization.

    Args:
        text_colors: 3D list of color codes for each word pair
        input_word: List of input word sequences
        output_word: List of output word sequences
        file_path: Directory path for saving HTML file
    """
    if file_path is None:
        file_path = os.getcwd()

    # Initialize HTML document structure
    html_content = build_html_header()

    # Add JavaScript color data
    html_content += generate_color_array(text_colors, output_word)

    # Add interactive JavaScript handlers
    html_content += generate_mouseover_handlers(input_word, output_word)

    # Close JavaScript section and add body
    html_content += close_script_and_add_body()

    # Generate HTML content for each sequence
    for sequence_idx in range(3):
        html_content += create_sequence_section(
            sequence_idx, input_word[sequence_idx], output_word[sequence_idx]
        )

        if sequence_idx < 2:
            html_content += add_section_separator()

    # Close HTML document
    html_content += close_html_document()

    # Write to file
    output_file = os.path.join(file_path, "connectivity.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)


def build_html_header():
    """Build the HTML document header with jQuery."""
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script>
        $(document).ready(function(){
        var col = ['''


def generate_color_array(text_colors, output_word):
    """Generate JavaScript color array from text_colors data."""
    color_array_content = ""

    for seq_idx in range(3):
        for word_idx in range(len(output_word[seq_idx])):
            color_array_content += "["

            # Add colors for each character
            colors_for_word = text_colors[seq_idx][word_idx]
            for color_idx, color in enumerate(colors_for_word):
                color_array_content += f'"{color}"'
                if color_idx < len(colors_for_word) - 1:
                    color_array_content += ","

            color_array_content += "],"

    # Remove trailing comma and close array
    return color_array_content.rstrip(",") + "];\n"


def generate_mouseover_handlers(input_word, output_word):
    """Generate JavaScript mouseover and mouseout event handlers."""
    handler_content = ""

    for seq_idx in range(3):
        for output_idx in range(len(output_word[seq_idx])):
            # Create mouseover handler
            handler_content += f'$(".h{seq_idx}{output_idx}").mouseover(function(){{\n'

            for input_idx in range(len(input_word[seq_idx])):
                color_ref = f"col[{output_idx}][{input_idx}]"
                handler_content += f'$(".t{seq_idx}{input_idx}").css("background-color", {color_ref});\n'

            handler_content += "});\n"

            # Create mouseout handler (reset all backgrounds)
            handler_content += f'$(".h{seq_idx}{output_idx}").mouseout(function(){{\n'

            for reset_seq in range(3):
                for reset_input in range(len(input_word[reset_seq])):
                    handler_content += f'$(".t{reset_seq}{reset_input}").css("background-color", "#ffff99");\n'

            handler_content += "});\n"

    return handler_content


def close_script_and_add_body():
    """Close JavaScript section and start HTML body."""
    return '''});
</script>
</head>
<body>
    <h1>Connectivity:</h1>
    <p>The connection strength between the target for the selected character and the input characters is highlighted in green (reset). Hover over the text to change the selected character.</p>
    <div style="background-color:#ffff99;color:black;padding:2%; margin:4%;">
    <p>
    <div>Output:</div>
    <div style='display:flex; border: 2px solid #d0cccc; padding: 8px; margin: 8px;'>'''


def create_sequence_section(seq_idx, input_sequence, output_sequence):
    """Create HTML section for one input/output sequence pair."""
    section_content = ""

    # Add output characters
    for char_idx, char in enumerate(output_sequence):
        section_content += f'\n\t<div class="h{seq_idx}{char_idx}">{char}</div>'

    section_content += '''</div>
    </p>
    <p>
    <div>Input:</div>
    <div style='display:flex; border: 2px solid #d0cccc; padding: 8px; margin: 8px;'>'''

    # Add input characters
    for char_idx, char in enumerate(input_sequence):
        section_content += f'\n\t<div class="t{seq_idx}{char_idx}">{char}</div>'

    return section_content


def add_section_separator():
    """Add separator between sections."""
    return '''</div></p></div><p></p></div>
    <div style="background-color:#ffff99;color:black;padding:2%; margin:4%;">
    <div>Output:</div>
    <div style='display:flex; border: 2px solid #d0cccc; padding: 8px; margin: 8px;'>'''


def close_html_document():
    """Close the HTML document structure."""
    return '''
        </div>
        </p>
        </div>
        </body>
</html>'''


def connectivity(input_words, rnn_type, file_path):
    """
    Main function to generate connectivity visualization HTML file.

    Args:
        input_words: List of 3 input word sequences
        rnn_type: Type of RNN model to use for inference
        file_path: Directory path for saving output file
    """
    # Initialize data containers
    processed_colors = []
    processed_input_words = []
    processed_output_words = []

    # Process each of the 3 input sequences
    for sequence_idx in range(3):
        # Get model predictions and attention weights
        predicted_output, processed_input, _, attention_matrix = inference_model(
            input_words[sequence_idx], rnn_type
        )

        # Convert attention weights to color codes
        sequence_colors = []
        for output_pos in range(len(predicted_output)):
            color_row = []
            for input_pos in range(len(attention_matrix[output_pos])):
                attention_value = attention_matrix[output_pos][input_pos]
                color_code = get_shade_color(attention_value)
                color_row.append(color_code)
            sequence_colors.append(color_row)

        # Store processed data
        processed_colors.append(sequence_colors)
        processed_input_words.append(processed_input)
        processed_output_words.append(predicted_output)

    # Generate HTML visualization file
    create_file(processed_colors, processed_input_words, processed_output_words, file_path)

def transliterate(input_word, rnn_type, file_name=None, visual_flag=True):
    # Set default file path if none is provided
    if file_name is None:
        file_name = os.path.join(os.getcwd(), "attention_heatmap.png")

    # Perform inference to get outputs
    predicted, cleaned_input, att_matrix, attention_weights_list = _run_inference(input_word, rnn_type)

    # Display the results
    _display_transliteration(cleaned_input, predicted)

    # Resize the attention matrix to match actual lengths
    att_matrix = att_matrix[:len(predicted), :len(cleaned_input)]

    # Generate and save the attention heatmap
    plot_attention(att_matrix, cleaned_input, predicted, file_name)

    # Optionally visualize attention weights step by step
    if visual_flag:
        visualize(cleaned_input, predicted, attention_weights_list)



def _run_inference(input_text, rnn_type):
    predicted_output, formatted_input, att_plot, attention_weights = inference_model(input_text, rnn_type)
    return predicted_output, formatted_input, att_plot, attention_weights


def _display_transliteration(source, prediction):
    print("\nInput:", source)
    print("Predicted transliteration:", prediction)

def generate_inputs(rnn_type, n_test_samples=10):
    # Load test input-target word pairs
    target_list, input_list = create_dataset(test_file_path)

    # Loop through requested number of test samples
    count = 0
    while count < n_test_samples:
        random_idx = _get_random_index(len(input_list))
        test_input = input_list[random_idx]
        save_path = _build_output_path(test_input)

        # First prediction with visualization
        if count == 0:
            transliterate(test_input[1:-1], rnn_type, save_path, visual_flag=True)
        else:
            transliterate(test_input[1:-1], rnn_type, save_path, visual_flag=False)

        count += 1


def _get_random_index(max_val):
    return random.randint(0, max_val - 1)


def _build_output_path(input_str):
    folder_path = os.path.join(os.getcwd(), "predictions_attention", str(run_name))
    file_name = input_str + ".png"
    return os.path.join(folder_path, file_name)

'''
Sweep configuration for hyper parameter tuning
'''
!pip install wandb --upgrade
import wandb
# !wandb login
wandb.login(key="7f46816d45e3df192c3053bab59032e9d710fef4")
sweep_config = {
    "name": "Bayesian Sweep without attention",
    "method": "bayes",
    "metric": {"name": "val_accuracy", "goal": "maximize"},
    "parameters": {

        "rnn_type": {"values": ["LSTM"]},  #RNN, GRU

        "embed": {"values": [256,512]},

        "latent": {"values": [512,1024]},

        "dropout": {"values": [0.1, 0.2, 0.3]},

        "epochs": {"values": [20]},

        "bs": {"values": [64]},


    },
  }

sweep_id = wandb.sweep(sweep_config, project="DA6401_Assignment3_attention", entity="cs24m034-indian-institute-of-technology-madras")

wandb.agent(sweep_id, train, count = 30)

# '''
# manual training for the best parameter model
# '''
# manual_train()

#Download a copy of the predictions_attention and training_checkpoints folder.
!zip -r /content/predictions_attention.zip /content/predictions_attention
!zip -r /content/training_checkpoints.zip /content/training_checkpoints
from google.colab import files
files.download("/content/predictions_attention.zip")
files.download("/content/training_checkpoints.zip")

