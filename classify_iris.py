import nltk
from nltk.corpus import names
import random
nltk.data.path.append("G:\\nltk_data")

def iris_features(arr):
    return {'sepal_length' : arr[0], 
            'sepal_width'  : arr[1],
            'petal_length' : arr[2],
            'petal_width'  : arr[3]
            }
            
labeled_iris = []
iris_filename = "G:\SachinK\progs\search\iris.txt"
with open(iris_filename, 'r') as f:
    next(f)
    for line in f:
        arr = line.split(",")
        labeled_iris.append((iris_features(arr[0:4]), arr[4]))

random.shuffle(labeled_iris)
print labeled_iris[-1]

train_set, test_set = labeled_iris[:100], labeled_iris[100:]
print len(train_set)
print len(test_set)
classifier = nltk.NaiveBayesClassifier.train(train_set)
print(nltk.classify.accuracy(classifier, test_set))

errors = []
for (features, tag) in test_set:
    guess = classifier.classify(features)
    if guess != tag:
        errors.append( (tag, guess, features))

print "Total errors = " + str(len(errors))
for (tag, guess, features) in sorted(errors):
    print('correct={:<8} guess={:<8s} features={:<30}'.format(tag, guess, features))
