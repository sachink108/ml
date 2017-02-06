import nltk
from nltk.corpus import names
import random
nltk.data.path.append("G:\\nltk_data")

def gender_features(word):
    return {'last_letter' : word[-1]}

labeled_names = ([(name, 'male') for name in names.words("male.txt")] + [(name, 'female') for name in names.words("female.txt")])
random.shuffle(labeled_names)

#featuresets = [(gender_features(n), gender) for (n, gender) in labeled_names]
#train_set, test_set = featuresets[500:], featuresets[:500]
#classifier = nltk.NaiveBayesClassifier.train(train_set)
train_names = labeled_names[1500:]
devtest_names = labeled_names[500:1500]
test_names = labeled_names[:500]

train_set = [(gender_features(n), gender) for (n, gender) in train_names]
devtest_set = [(gender_features(n), gender) for (n, gender) in devtest_names]
test_set = [(gender_features(n), gender) for (n, gender) in test_names]
classifier = nltk.NaiveBayesClassifier.train(train_set)
print(nltk.classify.accuracy(classifier, test_set))

#print classifier.classify(gender_features('Neo'))
#print classifier.classify(gender_features('Trinity'))

errors = []
correct = []
for (name, tag) in devtest_names:
    guess = classifier.classify(gender_features(name))
    if guess != tag:
        errors.append( (tag, guess, name) )

print "Total errors = " + str(len(errors))
for (tag, guess, name) in sorted(errors):
    print('correct={:<8} guess={:<8s} name={:<30}'.format(tag, guess, name))

