from nltk.corpus import movie_reviews
import random
import nltk
import os
import io
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer

stopWords = set(stopwords.words('english'))

class Document:
    def __init__(self, filename, category):
        self.file = filename
        self.category = category
        self.wordList = set()
        self.read() # this should be lazy initialization

    def getName(self):
        return self.file

    def read(self):
        tokenizer = RegexpTokenizer(r'\w+')
        stemmer = PorterStemmer()
        with io.open(self.file, "r", encoding="utf-8", errors='ignore') as my_file:
            tokens = tokenizer.tokenize(my_file.read())
            self.wordList.update(stemmer.stem(w.lower()) for w in tokens if not w in stopWords)
        #print ("Document %s has %d words" % (self.file, len(self.wordList)))

    def getAllWords(self):
        return self.wordList

class Corpus:
    def __init__(self, path):
        self.corpus = {}
        self.path = path
        self.allWords = set()
        self.init()

    def init(self):
        print ("Initializing Corpus from " + self.path)
        for dirpath, dirs, files in os.walk(self.path):
            nfiles = 0
            for name in files:
                nfiles += 1
                if nfiles == 10:
                    break
                filename = os.path.join(dirpath, name)
                category = filename.split("\\")[2]
                if (category not in self.corpus):
                    print ("Reading Category..." + category)
                    self.corpus[category] = list()
                self.corpus[category].append(Document(filename, category))
        self. printInfo()

    def printInfo(self):
        print ("Read %d categories from corpus" % len(self.corpus.keys()))
        print ("Category Wise Details")
        print ("---------------------")
        for cat in self.corpus:
            n = len(self.corpus[cat])
            print ("Category %s has %d documents" %(cat, n))

    def getCategories(self):
        return self.corpus.keys()

    def randomize(self):
        for cat in self.corpus: # this will randomize the documents
            random.shuffle(self.corpus[cat])

    def getCategoryTrainingSet(self, cat):
        return self.corpus[cat][:int(len(self.corpus[cat]) * 0.8)]

    def getCategoryTestingSet(self, cat):
        return self.corpus[cat][int(len(self.corpus[cat]) * 0.8):]

    def getTrainingSet(self):
        trainingSet = []
        for cat in self.corpus:
            ndocs = len(self.corpus[cat])
            trainingSet.extend(self.corpus[cat][:int(ndocs * 0.8)])
        return trainingSet

    def getTestingSet(self, cat):
        testingSet = []
        for cat in self.corpus:
            ndocs = len(self.corpus[cat])
            testingSet.extend(self.corpus[cat][int(ndocs * 0.8):])
        return testingSet

    def getAllWords(self):
        if (len(self.allWords) == 0):
            for cat in self.corpus:
                for doc in self.corpus[cat]:
                    self.allWords.update(doc.getAllWords())
            print ("Total Unique Words in the corpus = %d" % len(self.allWords))
        return self.allWords

    def getCategoryWords(self, category):
        catAllWords = []
        for doc in self.corpus[category]:
            catAllWords.extend(doc.getAllWords())
        return catAllWords

    def getDocumentFeatures(self, document):
        features = {}
        docWords = set(word for word in document.getAllWords())
        for word in self.getAllWords():
            features['contains({})'.format(word)] = (word in docWords)

        return features

def main():
    path = "data"
    corpus = Corpus(path)
    train_set = []
    print ("Generating training data...")
    for cat in corpus.getCategories():
        for doc in corpus.getCategoryTrainingSet(cat):
            train_set.append((corpus.getDocumentFeatures(doc), cat))
    print("finished")

    print ("Training Classifier...")
    classifier = nltk.NaiveBayesClassifier.train(train_set)
    print ("finished")
    test_set = []
    print("Generating test data...")
    for cat in corpus.getCategories():
        for doc in corpus.getCategoryTestingSet(cat):
            test_set.append((corpus.getDocumentFeatures(doc), cat))
    print ("finished")
    print ("Starting testing...")
    accuracyByCategory = dict
    for doc in test_set:
        print ("Doc class = " + doc[1] + " Classified as " + classifier.classify(doc[0]))

    #print ("Calculating Accuracy...")
    #accuracy = nltk.classify.accuracy(classifier, test_set)
    #print("Classifier Accuracy is %f" % accuracy)

if __name__ == '__main__':
    main()

