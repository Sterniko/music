""" This module prepares midi file data and feeds it to the neural
    network for training """
import glob
import pickle
import numpy
from music21 import converter, instrument, note, chord
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Activation
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint, CSVLogger, TerminateOnNaN

def train_network():
    """ Train a Neural Network to generate music """
    notes = get_notes()

    # get amount of pitch names
    n_vocab = len(set(notes))

    network_input, network_output = prepare_sequences(notes, n_vocab)

    model = create_network(network_input, n_vocab, len(notes))

    train(model, network_input, network_output)

def get_notes():
    """ Get all the notes and chords from the midi files in the ./midi_songs directory """
    notes = []

    for file in glob.glob("multiTrack/*.mid"):
        midi = converter.parse(file)

        print("Parsing %s" % file)

        notes_to_parse = None

        try: # file has instrument parts
            s2 = instrument.partitionByInstrument(midi)
            notes_to_parse = s2.parts[0].recurse() 
        except: # file has notes in a flat structure
            notes_to_parse = midi.flat.notes

        for element in notes_to_parse:
            if isinstance(element, note.Note):
                notes.append(str(element.pitch))
            elif isinstance(element, chord.Chord):
                notes.append('.'.join(str(n) for n in element.normalOrder))

    with open('data/notes', 'wb') as filepath:
        pickle.dump(notes, filepath)

    print("finished getting notes \n")
    return notes

def prepare_sequences(notes, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    print("sequence length \n")
    sequence_length = 50

    # get all pitch names
    print("pitchnames \n")
    pitchnames = sorted(set(item for item in notes))

     # create a dictionary to map pitches to integers
    print("creating dictionary \n")
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    network_input = []
    network_output = []

    
    # create input sequences and the corresponding outputs
    print("creating input sequence \n")
    print("notes length %d", len(notes))
    for i in range(0, int(len(notes)/10) - sequence_length, 1):
        
        sequence_in = notes[i:i + sequence_length]
        
        sequence_out = notes[i + sequence_length]
      
        network_input.append([note_to_int[char] for char in sequence_in])
       
        network_output.append(note_to_int[sequence_out])
    print("5")
    n_patterns = len(network_input)
    print("6")
    # reshape the input into a format compatible with LSTM layers
    network_input = numpy.reshape(network_input, (n_patterns, sequence_length, 1))
    print("7")
    # normalize input
    network_input = network_input / float(n_vocab)
    print("8")
    network_output = np_utils.to_categorical(network_output)
    print("return")
    return (network_input, network_output)

def create_network(network_input, n_vocab, noteslength):
    """ create the structure of the neural network """
    print("sequential")
    model = Sequential()
    print("model.add")
    model.add(LSTM(
        noteslength,
        input_shape=(network_input.shape[1], network_input.shape[2]),
        return_sequences=True
    ))
    print("dropout")
    model.add(Dropout(0.3))
    print("LSTM")
    model.add(LSTM(noteslength, return_sequences=True))
    print("dropout")
    model.add(Dropout(0.3))
    print("LSTM")
    model.add(LSTM(noteslength))
    print("Dense")
    model.add(Dense(noteslength/2))
    print("dropout")
    model.add(Dropout(0.3))
    print("Dense")
    model.add(Dense(n_vocab))
    print("activation")
    model.add(Activation('softmax'))
    print("compile")
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
    print("return")
    return model

def train(model, network_input, network_output):
    """ train the neural network """
    filepath = "weights-improvement-{epoch:02d}-{loss:.4f}-bigger.hdf5"
    checkpoint = ModelCheckpoint(
        filepath,
        monitor='loss',
        verbose=0,
        save_best_only=True,
        mode='min'
    )
    filepath_acc="CSV-DATEI.csv"
    accuracy = CSVLogger(filepath_acc, separator=',', append=False)

    callbacks_list = [checkpoint,accuracy, TerminateOnNaN()]

    history = model.fit(network_input, network_output, epochs=200, batch_size=(128*6), callbacks=callbacks_list)
    print(history.history.keys)

if __name__ == '__main__':
    train_network()
