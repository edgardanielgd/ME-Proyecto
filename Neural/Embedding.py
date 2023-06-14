import numpy as np
import nltk.corpus as corpus
from Utils import softmax, get_index_from_hot_encoding
import time

# Condense a word (represented as an array of 0s and a single 1) to 
# a vector of minor size


class Embedding:

    def __init__(self, size = 10, distance = 2):

        # Resulting vectors will have this size
        # Recall each vector represents one word
        self.size = size
        self.distance = distance
        self.x_training = None
        self.y_training = None
        self.dense_weights_1st = None
        self.dense_weights_2nd = None
        self.old_dense_weights_1st = None
        self.old_dense_weights_2nd = None
    
    def create_training_from_sentences(self, sentences, word_to_index, only_nexts = False):
        # IMPORTANT: Index is an array, not a number
        x_training = []
        y_training = []

        for sentence in sentences:
            # Iterate over each word in the sentence
            # Recall sentence is made up of arrays of word
            for i in range( len( sentence ) ):
                # Get the word and its context
                word = sentence[i]
                indexed_word = word_to_index[ word ]
                
                if( not only_nexts ):
                    # Generate for previous words
                    for j in range( max(0,i - self.distance), i ):
                        x_training.append( indexed_word )

                        # Get the context word
                        context_word = sentence[j]
                        indexed_pair_word = word_to_index[ context_word ]
                        y_training.append( indexed_pair_word )
                
                # Generate for next words
                for j in range( i + 1, min( len(sentence), i + self.distance + 1 ) ):
                    x_training.append( indexed_word )

                    # Get the context word
                    context_word = sentence[j]
                    indexed_pair_word = word_to_index[ context_word ]
                    y_training.append( indexed_pair_word )
                
        self.x_training = np.array( x_training )
        self.y_training = np.array( y_training )
        return self.x_training, self.y_training
    
    def special_train(self, sentence, word_to_index, learning_rate = 0.1 ):

        # First than all, check if we have done this before, and then, restore the base
        # weights
        if self.old_dense_weights_1st is not None and self.old_dense_weights_2nd is not None:
            self.dense_weights_1st = self.old_dense_weights_1st
            self.dense_weights_2nd = self.old_dense_weights_2nd
        
        # This additional training aims to adapt to user's inputs at a moment
        # So, lets say user types the sentence w0, w1, w2, ..., wi, wi+1, ..., wn
        for i in range( len( sentence ) ):
            # Get the word and its context
            word = sentence[i]

            if not word in word_to_index:
                # Word is not in the vocabulary
                continue

            indexed_word = word_to_index[ word ]
            x_train = indexed_word
            
            # Generate for inmediate next word
            if i < len( sentence ) - 1:
                context_word = sentence[i+1]

                if context_word not in word_to_index:
                    # Word is not in the vocabulary
                    continue

                indexed_pair_word = word_to_index[ context_word ]
                y_train = indexed_pair_word
            
            # Save old weights in haven't done it yet
            # In this way we will take into account user sentence precedence 
            # only until he deletes his phrase
            if self.old_dense_weights_1st is None or self.old_dense_weights_2nd is None:
                self.old_dense_weights_1st = self.dense_weights_1st
                self.old_dense_weights_2nd = self.dense_weights_2nd
            
            # Forward process
            A1 = np.dot( x_train, self.dense_weights_1st ) # 1xm * m*10 = 1x10
            A2 = np.dot( A1, self.dense_weights_2nd ) # 1x10 * 10xm = 1xm
            y_hat = softmax( A2 ) # 1xm

            # Backward process
            # Calculate the error
            A1_T = A1.T[:, np.newaxis] # 10x1
            error = (y_hat - y_train)[np.newaxis, :]  # 1xm - 1xm = 1xm
            #

            dw2 = np.outer( A1_T, error ) # 10x1 * 1xm = 10xm
            temp = np.dot( error, self.dense_weights_2nd.T ) # 1xm * mx10 = 1x10
            dw1 = np.outer( 
                x_train, 
                temp
            ) # mx1 * 1x10 = mx10

            # Update weights
            self.dense_weights_1st -= learning_rate * dw1
            self.dense_weights_2nd -= learning_rate * dw2

    def train(
            self, sentences, word_to_index, learning_rate = 0.01, only_nexts = False
        ):
        if self.x_training is None:
            self.create_training_from_sentences( sentences, word_to_index, only_nexts )
        
        # We got two layers, both dense ones and a softmax activation
        # for the output layer
        dense_weights_1st = np.random.rand( len( word_to_index ), self.size )
        dense_weights_2nd = np.random.rand( self.size, len( word_to_index ) )

        for i in range( len( self.x_training ) ):
            x_train = self.x_training[i]
            y_train = self.y_training[i]

            # Forward process
            A1 = np.dot( x_train, dense_weights_1st ) # 1xm * m*10 = 1x10
            A2 = np.dot( A1, dense_weights_2nd ) # 1x10 * 10xm = 1xm
            y_hat = softmax( A2 ) # 1xm

            # Backward process
            # Calculate the error

            # TODO: Maybe could use cross entropy as well
            #
            A1_T = A1.T[:, np.newaxis] # 10x1
            error = (y_hat - y_train)[np.newaxis, :]  # 1xm - 1xm = 1xm
            #

            dw2 = np.outer( A1_T, error ) # 10x1 * 1xm = 10xm
            temp = np.dot( error, dense_weights_2nd.T ) # 1xm * mx10 = 1x10
            dw1 = np.outer( 
                x_train, 
                temp
            ) # mx1 * 1x10 = mx10

            # Update weights
            dense_weights_1st -= learning_rate * dw1
            dense_weights_2nd -= learning_rate * dw2

        # Save weights for future crazy stuff
        self.dense_weights_1st = dense_weights_1st
        self.dense_weights_2nd = dense_weights_2nd
    
    def predict(self, word, word_to_index, index_to_word, generate_indexed_word = False):
        # Get the index of the word
        indexed_word = word_to_index[ word ]

        # Forward process
        A1 = np.dot( indexed_word, self.dense_weights_1st )
        A2 = np.dot( A1, self.dense_weights_2nd )
        y_hat = softmax( A2, generate_indexed_word )

        if not generate_indexed_word:
            return y_hat

        return index_to_word[ get_index_from_hot_encoding( y_hat ) ]
    
    def get_embedding(self, word, word_to_index):
        # Get the index of the word
        indexed_word = word_to_index[ word ]

        # Forward process
        A1 = np.dot( indexed_word, self.dense_weights_1st )
        return A1
    
    def save_weights(self, path):
        np.save( path + "dense_weights_1st", self.dense_weights_1st )
        np.save( path + "dense_weights_2nd", self.dense_weights_2nd )

    def load_weights(self, path):
        self.dense_weights_1st = np.load( path + "dense_weights_1st.npy" )
        self.dense_weights_2nd = np.load( path + "dense_weights_2nd.npy" )

# print( len(corpus.brown.words( fileids= ["ca33","cj30","cj31"] ) ))
# print( len( corpus.treebank.words( fileids = ["wsj_0001.mrg","wsj_0002.mrg","wsj_0003.mrg"] ) ) )
# print( len( corpus.treebank.sents( fileids = ["wsj_0001.mrg","wsj_0002.mrg","wsj_0003.mrg"] ) ) )