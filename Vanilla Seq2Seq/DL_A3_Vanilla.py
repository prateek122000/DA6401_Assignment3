# -*- coding: utf-8 -*-

import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import copy

#Downloading the Dakshina Dataset

'''
Downloading the data
'''
!curl https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar --output daksh.tar

'''
Capturing the data and saving as the Tar file
'''
!tar -xvf  'daksh.tar'

def tokenizeTensor(texts, tokenizer=None):
    if tokenizer is None:
        tokenizer = tf.keras.preprocessing.text.Tokenizer(char_level=True, filters='')
        tokenizer.fit_on_texts(texts)

    encoded = tokenizer.texts_to_sequences(texts)
    padded_result = tf.keras.preprocessing.sequence.pad_sequences(encoded, padding='post')

    return padded_result, tokenizer

'''
Function to read the data
Input - Data path to read the data
Output - input text, target text, input and target tokenizier, input and target tensor
'''



def data(path, input_tokenizer=None, output_tokenizer=None, input_length=None, output_length=None):
    input_texts = []   # stores source sentences
    target_texts = []  # stores target sentences

    # Load and shuffle the dataset if tokenizers are not provided
    dataset = pd.read_csv(path, sep="\t", names=["col1", "col2", "col3"]).astype(str)
    if input_tokenizer is None:
        dataset = dataset.sample(frac=1).reset_index(drop=True)

    # Preprocess each row
    for _, row in dataset.iterrows():
        source = row["col3"]
        target = row["col2"]
        if source == '</s>' or target == '</s>':
            continue
        # Add start and end tokens to target
        target = "\t" + target + "\n"
        input_texts.append(source)
        target_texts.append(target)

    # Tokenize the inputs and outputs
    input_tensor, input_tokenizer = tokenizeTensor(input_texts, input_tokenizer)
    target_tensor, output_tokenizer = tokenizeTensor(target_texts, output_tokenizer)

    # Optional: pad tensors to specified lengths
    if input_length is not None and output_length is not None:
        input_padding = input_length - input_tensor.shape[1]
        output_padding = output_length - target_tensor.shape[1]

        if input_padding > 0:
            input_tensor = tf.concat(
                [input_tensor, tf.zeros((input_tensor.shape[0], input_padding), dtype=input_tensor.dtype)],
                axis=1
            )
        if output_padding > 0:
            target_tensor = tf.concat(
                [target_tensor, tf.zeros((target_tensor.shape[0], output_padding), dtype=target_tensor.dtype)],
                axis=1
            )

    # Return texts, tensors, and tokenizers
    return input_texts, input_tensor, input_tokenizer, target_texts, target_tensor, output_tokenizer

# Commented out IPython magic to ensure Python compatibility.
# # Preprocessing and reading the training data
# %%capture
# input_texts,input_tensor,input_tokenizer,target_texts,target_tensor,target_tokenizer=data("/content/dakshina_dataset_v1.0/hi/lexicons/hi.translit.sampled.train.tsv")
# 
#

# Commented out IPython magic to ensure Python compatibility.
# # Preprocessing and reading the validation data
# %%capture
# val_input_texts,val_input_tensor,val_input_tokenizer,val_target_texts,val_target_tensor,val_target_tokenizer=data("/content/dakshina_dataset_v1.0/hi/lexicons/hi.translit.sampled.dev.tsv",input_tokenizer,target_tokenizer,input_tensor.shape[1],target_tensor.shape[1])
#

# Commented out IPython magic to ensure Python compatibility.
# # Preprocessing and reading the testing data
# %%capture
# test_input_texts,test_input_tensor,test_input_tokenizer,test_target_texts,test_target_tensor,test_target_tokenizer=data("/content/dakshina_dataset_v1.0/hi/lexicons/hi.translit.sampled.test.tsv",input_tokenizer,target_tokenizer,input_tensor.shape[1],target_tensor.shape[1])
#

# --- Token and Sequence Configuration ---
encoder_vocab_size = len(input_tokenizer.word_index) + 1  # encoder vocabulary size
decoder_vocab_size = len(target_tokenizer.word_index) + 1  # decoder vocabulary size
max_encoder_length = input_tensor.shape[1]                # maximum encoder sequence length
max_decoder_length = target_tensor.shape[1]                # maximum decoder sequence length

# Reverse lookup: index -> character
encoder_index_to_char = {idx: char for char, idx in input_tokenizer.word_index.items()}
decoder_index_to_char = {idx: char for char, idx in target_tokenizer.word_index.items()}

# --- Model Builder ---
def build_model(rnn_type, embedding_dim, encoder_layers, decoder_layers, dropout):
    """
    Constructs a sequence-to-sequence model with configurable RNN cell type.

    Args:
        rnn_type (str): 'LSTM', 'GRU', or 'RNN'.
        embedding_dim (int): dimension of embedding vectors.
        encoder_layers (int): number of stacked encoder RNN layers.
        decoder_layers (int): number of stacked decoder RNN layers.
        dropout (float): dropout rate for all RNN layers.

    Returns:
        keras.Model: compiled seq2seq model.
    """
    # Map type string to actual Keras layer class
    cell_map = {
        'LSTM': keras.layers.LSTM,
        'GRU': keras.layers.GRU,
        'RNN': keras.layers.SimpleRNN
    }
    rnn_cell = cell_map.get(rnn_type)
    assert rnn_cell, f"Unsupported rnn_type: {rnn_type}"

    # --- Encoder ---
    enc_inputs = keras.Input(shape=(max_encoder_length,), name='encoder_inputs')
    enc_emb = keras.layers.Embedding(encoder_vocab_size, embedding_dim, name='encoder_embedding')(enc_inputs)

    # Stack RNN layers for encoder
    enc_output = enc_emb
    enc_states = []
    for i in range(encoder_layers):
        is_final = (i == encoder_layers - 1)
        if is_final:
            # final encoder returns states
            if rnn_type == 'LSTM':
                enc_out, state_h, state_c = rnn_cell(latent_dim,
                                                     return_sequences=False,
                                                     return_state=True,
                                                     dropout=dropout,
                                                     name=f'encoder_{i}')(enc_output)
                enc_states = [state_h, state_c]
            else:
                enc_out, state = rnn_cell(latent_dim,
                                          return_sequences=False,
                                          return_state=True,
                                          dropout=dropout,
                                          name=f'encoder_{i}')(enc_output)
                enc_states = [state]
        else:
            # intermediate encoder returns full sequence
            enc_out = rnn_cell(latent_dim,
                               return_sequences=True,
                               dropout=dropout,
                               name=f'encoder_{i}')(enc_output)
        enc_output = enc_out

    # --- Decoder ---
    dec_inputs = keras.Input(shape=(max_decoder_length,), name='decoder_inputs')
    dec_emb = keras.layers.Embedding(decoder_vocab_size, embedding_dim, name='decoder_embedding')(dec_inputs)

    dec_output = dec_emb
    last_dec_output = None
    for j in range(decoder_layers):
        is_final_dec = (j == decoder_layers - 1)
        return_seq = True  # always return sequence for stacking
        if is_final_dec:
            # final decoder, we only need output sequences (we don't use states further)
            return_state_flag = False
        else:
            return_state_flag = False

        # invoke decoder cell with initial state from encoder
        if rnn_type == 'LSTM':
            dec_cell = keras.layers.LSTM(latent_dim,
                                         return_sequences=True,
                                         return_state=True,
                                         dropout=dropout,
                                         name=f'decoder_{j}')
            if j == 0:
                out_seq, _, _ = dec_cell(dec_output, initial_state=enc_states)
            else:
                out_seq, _, _ = dec_cell(last_dec_output, initial_state=enc_states)
        else:
            dec_cell = cell_map[rnn_type](latent_dim,
                                          return_sequences=True,
                                          return_state=True,
                                          dropout=dropout,
                                          name=f'decoder_{j}')
            if j == 0:
                out_seq, _ = dec_cell(dec_output, initial_state=enc_states)
            else:
                out_seq, _ = dec_cell(last_dec_output, initial_state=enc_states)
        last_dec_output = out_seq

    # Final dense projection
    dec_dense = keras.layers.Dense(decoder_vocab_size, activation='softmax', name='decoder_output_dense')
    dec_outputs = dec_dense(last_dec_output)

    # Define and return the model
    model = keras.Model([enc_inputs, dec_inputs], dec_outputs, name='seq2seq_model')
    return model






'''
Function - inferencing
Inputs -
  model
  encoder_layers
  decoder_layers
Output - encoder model and the deocder model separately
'''


def inferencing(model, encoder_layers, decoder_layers):
    """
    Split a trained seq2seq model into separate encoder and decoder inference models.

    Args:
        model (keras.Model): trained seq2seq model.
        encoder_layers (int): number of encoder RNN layers used during training.
        decoder_layers (int): number of decoder RNN layers used during training.

    Returns:
        (encoder_model, decoder_model): two keras Models for inference.
    """
    # --- Encoder Inference ---
    encoder_input = model.input[0]

    # Locate final encoder layer by offset from inputs
    # Encoder cells follow: Input -> embedding -> encoder layers...
    encoder_cell = model.layers[2 + encoder_layers]
    if isinstance(encoder_cell, keras.layers.LSTM):
        _, state_h, state_c = encoder_cell.output
        encoder_states = [state_h, state_c]
    else:
        _, state = encoder_cell.output
        encoder_states = [state]

    encoder_model = keras.Model(inputs=encoder_input, outputs=encoder_states,
                                name='encoder_inference')

    # --- Decoder Inference ---
    # Single-step decoder input token
    single_dec_input = keras.Input(shape=(1,), name='dec_input_token')
    # Reuse embedding from trained model
    dec_embed_layer = model.get_layer('decoder_embedding')
    dec_input_embedded = dec_embed_layer(single_dec_input)

    # Prepare placeholders for decoder initial states
    dec_state_inputs = []
    dec_states_outputs = []
    prev_output = None

    for idx in range(decoder_layers):
        # Identify the trained decoder cell by name or position
        cell_layer = model.get_layer(f'decoder_{idx}')

        if isinstance(cell_layer, keras.layers.LSTM):
            # Two state vectors for LSTM
            h_input = keras.Input(shape=(latent_dim,), name=f'dec_h_in_{idx}')
            c_input = keras.Input(shape=(latent_dim,), name=f'dec_c_in_{idx}')
            init_states = [h_input, c_input]

            if idx == 0:
                out_seq, h_out, c_out = cell_layer(dec_input_embedded,
                                                   initial_state=encoder_states)
            else:
                out_seq, h_out, c_out = cell_layer(prev_output,
                                                   initial_state=init_states)

            dec_state_inputs += [h_input, c_input]
            dec_states_outputs += [h_out, c_out]

        else:
            # Single state for GRU or SimpleRNN
            s_input = keras.Input(shape=(latent_dim,), name=f'dec_s_in_{idx}')
            init_states = [s_input]

            if idx == 0:
                out_seq, s_out = cell_layer(dec_input_embedded,
                                            initial_state=encoder_states)
            else:
                out_seq, s_out = cell_layer(prev_output,
                                            initial_state=init_states)

            dec_state_inputs.append(s_input)
            dec_states_outputs.append(s_out)

        prev_output = out_seq

    # Final dense layer for token probabilities
    final_dense = model.get_layer('final')
    dec_token_probs = final_dense(prev_output)

    # Construct decoder inference model
    decoder_model = keras.Model(
        inputs=[single_dec_input] + dec_state_inputs,
        outputs=[dec_token_probs] + dec_states_outputs,
        name='decoder_inference'
    )

    return encoder_model, decoder_model




def do_predictions(input_seq, encoder_model, decoder_model,
                   batch_size, encoder_layers, decoder_layers,
                   target_tokenizer, index_to_char_target,
                   max_decoder_seq_length, rnn_type='LSTM'):
    """
    Decode a batch of sequences to generate target predictions.
    """
    # Encode input and prepare initial decoder states
    states = encoder_model.predict(input_seq)
    # Ensure states is a list for RNN/GRU
    if rnn_type in ('GRU', 'RNN'):
        states = [states]
    # Repeat state list for each decoder layer
    decoder_states = states * decoder_layers

    # Initialize target indices with start token '\t'
    start_idx = target_tokenizer.word_index['\t']
    prev_indices = np.full((batch_size, 1), start_idx, dtype=int)

    # Prepare containers for outputs
    predictions = [''] * batch_size
    finished = np.zeros(batch_size, dtype=bool)

    for _ in range(max_decoder_seq_length):
        # Predict next token and new states
        outputs = decoder_model.predict([prev_indices] + decoder_states)
        probs = outputs[0]
        decoder_states = outputs[1:]

        # Choose highest-probability token for each sequence
        next_indices = np.argmax(probs[:, -1, :], axis=-1)
        prev_indices[:, 0] = next_indices

        for i, token_idx in enumerate(next_indices):
            if finished[i]:
                continue
            # Map token index to character
            if token_idx == 0:
                char = '\n'
            else:
                char = index_to_char_target[token_idx]

            # Check for end token
            if char == '\n':
                finished[i] = True
            else:
                predictions[i] += char

        # Stop early if all sequences have finished
        if finished.all():
            break

    return predictions


def test_accuracy(encoder_model, decoder_model,
                  test_input_tensor, test_input_texts, test_target_texts,
                  target_tokenizer, index_to_char_target,
                  encoder_layers, decoder_layers,
                  max_decoder_seq_length, rnn_type='LSTM',
                  success_path="success_predictions.txt",
                  failure_path="failure_predictions.txt"):
    """
    Compute word-level accuracy on the test set, logging successes and failures.
    """
    batch_size = test_input_tensor.shape[0]
    preds = do_predictions(
        input_seq=test_input_tensor,
        encoder_model=encoder_model,
        decoder_model=decoder_model,
        batch_size=batch_size,
        encoder_layers=encoder_layers,
        decoder_layers=decoder_layers,
        target_tokenizer=target_tokenizer,
        index_to_char_target=index_to_char_target,
        max_decoder_seq_length=max_decoder_seq_length,
        rnn_type=rnn_type
    )

    success_count = 0
    # Open files once
    with open(success_path, 'a') as succ_f, open(failure_path, 'a') as fail_f:
        for inp_text, true_text, pred in zip(
                test_input_texts, test_target_texts, preds):
            true = true_text[1:-1]
            if pred == true:
                success_count += 1
                succ_f.write(f"{inp_text} {true} {pred}\n")
            else:
                fail_f.write(f"{inp_text} {true} {pred}\n")

    return success_count / batch_size


def batch_validate(encoder_model, decoder_model,
                   val_input_tensor, val_target_texts,
                   target_tokenizer, index_to_char_target,
                   encoder_layers, decoder_layers,
                   max_decoder_seq_length, rnn_type='LSTM'):
    """
    Validate on the entire validation batch and return accuracy.
    """
    batch_size = val_input_tensor.shape[0]
    preds = do_predictions(
        input_seq=val_input_tensor,
        encoder_model=encoder_model,
        decoder_model=decoder_model,
        batch_size=batch_size,
        encoder_layers=encoder_layers,
        decoder_layers=decoder_layers,
        target_tokenizer=target_tokenizer,
        index_to_char_target=index_to_char_target,
        max_decoder_seq_length=max_decoder_seq_length,
        rnn_type=rnn_type
    )

    correct = sum(
        pred == target[1:-1]
        for pred, target in zip(preds, val_target_texts)
    )

    return correct / batch_size




#Training for Wandb Hyper parameter sweeping

#defining globals
rnn_type=None
embedding_dim=None
model= None
latent_dim = None
enc_layers=None
dec_layers=None
'''
Function- train()
Performs the entire training using Wandb sweeps
'''




def train():
    global rnn_type
    global embedding_dim
    global model
    global latent_dim
    global enc_layer
    global dec_layer

    # Initialize Weights and Biases
    wandb.init()

    # Assign configuration values to global variables
    rnn_type = wandb.config.rnn_type
    embedding_dim = wandb.config.embedding_dim
    latent_dim = wandb.config.latent_dim
    enc_layer = wandb.config.enc_layer
    dec_layer = wandb.config.dec_layer
    dropout = wandb.config.dropout
    epochs = wandb.config.epochs
    bs = wandb.config.bs

    # Set a descriptive name for the current run
    wandb.run.name = f"epochs_{epochs}_bs_{bs}_rnn_type_{rnn_type}_em_{embedding_dim}_latd_{latent_dim}_encs_{enc_layer}_decs_{dec_layer}_dr_{dropout}"

    # Construct and compile the model
    model = build_model(
        rnn_type=rnn_type,
        embedding_dim=embedding_dim,
        encoder_layers=enc_layer,
        decoder_layers=dec_layer,
        dropout=dropout
    )
    model.compile(
        optimizer="adam",
        loss=keras.losses.SparseCategoricalCrossentropy(reduction="none"),
        metrics=["accuracy"]
    )

    # Train for specified number of epochs
    for epoch_index in range(epochs):
        history = model.fit(
            [input_tensor, target_tensor],
            tf.concat([target_tensor[:, 1:], tf.zeros((target_tensor.shape[0], 1))], axis=1),
            batch_size=bs,
            epochs=1,
            shuffle=True
        )

        # Save model after each epoch
        model.save("vanilla.keras")

        # Load the saved model and setup inference models
        loaded_model = keras.models.load_model("/content/vanilla.keras")
        encoder_model, decoder_model = inferencing(
            loaded_model,
            encoder_layers=enc_layer,
            decoder_layers=dec_layer
        )

        # Log training loss to wandb
        wandb.log({"train_loss": history.history['loss'][0]})

    # Compute validation accuracy and log to wandb
    validation_accuracy = batch_validate(encoder_model, decoder_model, enc_layer, dec_layer)
    wandb.log({"val_acc": validation_accuracy})








#Manual Training

#defining globals
rnn_type=None
embedding_dim=None
model= None
latent_dim = None
enc_layers=None
dec_layers=None
'''
Function - Manual Train
perform the training manually for the best configuration
'''

def manual_train(config):
    global rnn_type
    global embedding_dim
    global model
    global latent_dim
    global enc_layer
    global dec_layer

    # Assign hyperparameters from the provided config
    rnn_type = config.rnn_type
    embedding_dim = config.embedding_dim
    latent_dim = config.latent_dim
    enc_layer = config.enc_layer
    dec_layer = config.dec_layer
    dropout = config.dropout
    epochs = config.epochs
    bs = config.bs

    # Construct the sequence-to-sequence model
    model = build_model(
        rnn_type=rnn_type,
        embedding_dim=embedding_dim,
        encoder_layers=enc_layer,
        decoder_layers=dec_layer,
        dropout=dropout
    )

    # Compile model with specified loss and optimizer
    model.compile(
        optimizer="adam",
        loss=keras.losses.SparseCategoricalCrossentropy(reduction="none"),
        metrics=["accuracy"]
    )

    # Save a visualization of the model architecture
    tf.keras.utils.plot_model(
        model,
        to_file='model.png',
        show_shapes=True,
        show_dtype=True,
        show_layer_names=True,
        dpi=96
    )

    ###################################################### Training Loop ######################################################
    for epoch_num in range(epochs):
        history = model.fit(
            [input_tensor, target_tensor],
            tf.concat(
                [target_tensor[:, 1:], tf.zeros((target_tensor.shape[0], 1))],
                axis=1
            ),
            batch_size=bs,
            epochs=1,
            shuffle=True
        )

        # Save model to disk after each epoch
        model.save("vanilla.keras")

        # Load model and extract encoder/decoder components for evaluation
        trained_model = keras.models.load_model("/content/vanilla.keras")
        encoder_model, decoder_model = inferencing(
            trained_model,
            encoder_layers=enc_layer,
            decoder_layers=dec_layer
        )

        # Compute and display validation accuracy
        val_acc = batch_validate(encoder_model, decoder_model, enc_layer, dec_layer)
        print("Validation Accuracy:", val_acc)

    # Final evaluation on test data
    test_acc = test_accuracy(encoder_model, decoder_model, enc_layer, dec_layer)
    print("Test Accuracy:", test_acc)









# Install wandb (only needs to be done once)
!pip install -q wandb

# Import wandb after installation
import wandb

# Enable wandb logging
wb = True

if wb:
    wandb.login(key="7f46816d45e3df192c3053bab59032e9d710fef4")











# generating the wandb sweep configuration
if wb:
  sweep_config = {
    "name": "Bayesian Sweep without attention",
    "method": "bayes", #method used was bayesian
    "metric": {"name": "val_acc", "goal": "maximize"}, #mximizing the validation accuracy
    "parameters": {

        "rnn_type": {"values": ["LSTM"]}, #GRU, RNN

        "embedding_dim": {"values": [64,256,512]},

        "latent_dim": {"values": [256,512,1024]},

        "enc_layer": {"values": [1, 2]},

        "dec_layer": {"values": [1, 2]},

        "dropout": {"values": [0.3, 0.5]},

        "epochs": {"values": [10]},

        "bs": {"values": [32, 64]},


    },
  }





  #creating the wandb sweep
  sweep_id = wandb.sweep(sweep_config, project="DA6401_Assignment3_vanilla", entity="cs24m034-indian-institute-of-technology-madras")
  #calling the wandb sweep to start the hyper parameter tuning.
  wandb.agent(sweep_id, train, count = 30)



