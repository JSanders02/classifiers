from argparse import ArgumentParser
from scipy.stats import multivariate_normal
import numpy as np

parser = ArgumentParser()
parser.add_argument("file", type=str, help="the name of your dataset")
parser.add_argument("-m", "--method", type=str, choices=["onefile", "loo", "traintest"], default="onefile",
                    help="bayesian classification method - onefile (default), loo, traintest (training/testing data in "
                         "separate files, appended with _train and _test, respectively)")

args = parser.parse_args()

DATASET = args.file
METHOD = args.method

if METHOD == "traintest":
    X = np.loadtxt(open(f'data/{DATASET}_train.txt', 'r'), delimiter=",")
else:
    X = np.loadtxt(open(f'data/{DATASET}.txt', 'r'), delimiter=",")


def estimate_params(xs: np.array, n_factor: float = 0.1):
    # Regularise covariance - add small constant to diagonal to ensure symmetric positive definite
    regularise_cov = np.cov(xs, rowvar=False) + n_factor * np.identity(xs.shape[1])
    return np.mean(xs, axis=0), regularise_cov


# split data into training and testing sets
def split_data(xs: np.array, leave_out: int = False):
    if leave_out:
        return np.delete(xs, leave_out), xs[leave_out]
    else:
        return xs[0::2], xs[1::2]


# Find class labels and set up training and testing arrays
labels = np.unique(X[:, -1])

train_data = np.array([None for _ in labels])

if METHOD == "traintest":
    for i in range(len(labels)):
        train_data[i] = X[X[:, -1] == labels[i]]

    test_data = np.loadtxt(open(f'data/{DATASET}_test.txt', 'r'), delimiter=",")

else:
    test_data = np.array([None for _ in labels])

    for i in range(len(labels)):
        train_data[i], test_data[i] = split_data(X[X[:, -1] == labels[i]])

    test_data = np.vstack(tuple(test_data))

## TODO - loo testing

# Estimate priors - assume distribution within training data is accurate to real-world distribution
priors = [len(t) / len(np.vstack(tuple(train_data))) for t in train_data]

params = [estimate_params(xs[:, :-1]) for xs in train_data]

# Construct gaussian distributions using estimated parameters
normals = [multivariate_normal(mean=p[0], cov=p[1]) for p in params]

# Bayes classification rule - posterior probability {P(w|x)} = likelihood {P(x|w)} * prior
posteriors = np.array([n.pdf(test_data[:, :-1]) for n in normals]).T * priors

percent_right = np.count_nonzero(np.argmax(posteriors, axis=1) + 1 == test_data[:, -1]) / len(test_data) * 100
print(f'\nClassified {round(percent_right, 2)}% of the testing data correctly (2D.P.)')
