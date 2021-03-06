# coding: utf-8
import numpy as np
from scipy.spatial import distance
from word2vec.utils import unitvec


class WordVectors(object):

    def __init__(self, vocab=None, vectors=None, saveMemory=True):
        self.vocab = vocab
        if not saveMemory:
            self.vectors = vectors
        self.l2norm = np.vstack(unitvec(vec) for vec in vectors)

    def ix(self, word):
        '''
        Returns the index on self.vocab and self.l2norm for `word`
        '''
        temp = np.where(self.vocab == word)[0]
        if temp.size == 0:
            raise KeyError('Word not in vocabulary')
        else:
            return temp[0]

    def get_vector(self, word):
        '''
        Returns the vector for `word`
        '''
        idx = self.ix(word)
        return self.l2norm[idx]

    def get_l2_vector(self, word):
        '''
        Returns the l2-norm vector for `word`
        '''
        idx = self.ix(word)
        return self.l2norm[idx]

    def __getitem__(self, word):
        return self.get_vector(word)

    def generate_response(self, indexes, metric, exclude=''):
        '''
        Generates a response as a list of tuple based on the indexes
        Each tuple is: (word, metric)
        '''
        if isinstance(exclude, basestring):
            exclude = [exclude]
        return [(word, sim) for word, sim in zip(self.vocab[indexes], metric[indexes]) if word not in exclude]

    def cosine(self, word, n=10):
        '''
        Cosine similarity.

        metric = dot(l2norm_of_vectors, l2norm_of_target_vector)
        Uses a precomputed l2norm of the vectors
        '''
        metric = np.dot(self.l2norm, self.get_l2_vector(word))
        best = np.argsort(metric)[::-1][:n + 1]
        return self.generate_response(best, metric, exclude=word)

    def _cosine(self, word, n=10):
        '''
        Cosine distance using scipy.distance.cosine

        Note: This method is **a lot** slower than `self.cosine`
        and results are the almost the same, really just use `self.cosine`
        This is just available for testing.
        Requires saveMemory=False

        Parameters
        ----------
        word : string
            word in the vocabulary to calculate the vectors
        n : int, optional (default 10)
            number of neighbors to return
        '''
        target_vec = self[word]
        metric = np.empty(self.vocab.shape)
        for idx, vector in enumerate(self.vectors):
            metric[idx] = distance.cosine(target_vec, vector)

        best = metric.argsort()[:n + 1]
        return self.generate_response(best, metric, exclude=word)

    def analogy(self, pos, neg, n=10):
        '''
        Analogy similarity.

        Parameters
        ----------
        pos : list
        neg : list

        Example
        -------
            king - man + woman = queen | will be:
            pos=['king', 'woman'], neg=['man']
        '''
        words = pos + neg

        pos = [(word, 1.0) for word in pos]
        neg = [(word, -1.0) for word in neg]

        mean = []
        for word, direction in pos + neg:
            mean.append(direction * unitvec(self.get_vector(word)))
        mean = np.array(mean).mean(axis=0)

        similarities = np.dot(self.l2norm, mean)
        best = np.argsort(similarities)[::-1][:n + len(words) - 1]
        return [(_word, sim) for _word, sim in zip(self.vocab[best], similarities[best]) if _word not in words]


class WordClusters(object):
    def __init__(self, fname=None):
        if fname is not None:
            self.load(fname)

    def load(self, fname):
        self.words = np.genfromtxt(fname, dtype=object, delimiter=' ', usecols=0)
        self.clusters = np.genfromtxt(fname, dtype=int, delimiter=' ', usecols=1)
