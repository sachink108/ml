import nltk
nltk.data.path.append("c:\nltk_data")
from nltk.corpus import names
import random

def iris_features(f):
    return {'sepal_length':f[0], 'sepal_width': f[1], 'petal_length':f[2], 'petal_width':f[3]}

featuresets = [];
with open('iris.data') as f:
    for line in f.readlines():
        features = line.split(',')
        featuresets.append((iris_features(features), features[4].strip()))

random.shuffle(featuresets)
train_set, test_set = featuresets[:100], featuresets[100:]
classifier = nltk.NaiveBayesClassifier.train(train_set)
for t in test_set:
    print("actual={}, classified={}".format(t[1], classifier.classify(t[0])))
   
print ("Accuracy = {}".format(nltk.classify.accuracy(classifier, test_set)))
classifier.show_most_informative_features(5)
