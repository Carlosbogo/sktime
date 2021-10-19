# -*- coding: utf-8 -*-
"""Random Interval Classifier.

Pipeline classifier using summary statistics extracted from random intervals and an
estimator.
"""

__author__ = ["MatthewMiddlehurst"]
__all__ = ["RandomIntervalClassifier"]

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from sktime.base._base import _clone_estimator
from sktime.classification.base import BaseClassifier
from sktime.transformations.panel.random_intervals import RandomIntervals


class RandomIntervalClassifier(BaseClassifier):
    """Random interval classifier.

    This classifier simply transforms the input data using the RandomIntervals
    transformer and builds a provided estimator using the transformed data.

    Parameters
    ----------
    n_intervals=100,

    transformers=None,

    estimator : sklearn classifier, default=None
        An sklearn estimator to be built using the transformed data. Defaults to a
        Random Forest with 200 trees.
    n_jobs : int, default=1
        The number of jobs to run in parallel for both `fit` and `predict`.
        ``-1`` means using all processors.
    random_state : int or None, default=None
        Seed for random, integer.

    Attributes
    ----------
    n_classes_ : int
        Number of classes. Extracted from the data.
    classes_ : ndarray of shape (n_classes)
        Holds the label for each class.

    See Also
    --------
    RandomIntervals

    Examples
    --------
    >>> from sktime.classification.feature_based import RandomIntervalClassifier
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from sktime.datasets import load_unit_test
    >>> X_train, y_train = load_unit_test(split="train", return_X_y=True)
    >>> X_test, y_test = load_unit_test(split="test", return_X_y=True)
    >>> clf = RandomIntervalClassifier(
    ...     n_intervals=5,
    ...     estimator=RandomForestClassifier(n_estimators=10),
    ... )
    >>> clf.fit(X_train, y_train)
    RandomIntervalClassifier(...)
    >>> y_pred = clf.predict(X_test)
    """

    _tags = {
        "capability:multivariate": True,
        "capability:multithreading": True,
    }

    def __init__(
        self,
        n_intervals=None,
        interval_transformers=None,
        estimator=None,
        n_jobs=1,
        random_state=None,
    ):
        self.n_intervals = n_intervals
        self.interval_transformers = interval_transformers
        self.estimator = estimator

        self.n_jobs = n_jobs
        self.random_state = random_state

        self._transformer = None
        self._estimator = None

        super(RandomIntervalClassifier, self).__init__()

    def _fit(self, X, y):
        self._transformer = RandomIntervals(
            n_intervals=self.n_intervals,
            transformers=self.interval_transformers,
            random_state=self.random_state,
            n_jobs=self._threads_to_use,
        )

        self._estimator = _clone_estimator(
            RandomForestClassifier(n_estimators=200)
            if self.estimator is None
            else self.estimator,
            self.random_state,
        )

        m = getattr(self._estimator, "n_jobs", None)
        if m is not None:
            self._estimator.n_jobs = self._threads_to_use

        X_t = self._transformer.fit_transform(X, y)
        self._estimator.fit(X_t, y)

        return self

    def _predict(self, X):
        return self._estimator.predict(self._transformer.transform(X))

    def _predict_proba(self, X):
        m = getattr(self._estimator, "predict_proba", None)
        if callable(m):
            return self._estimator.predict_proba(self._transformer.transform(X))
        else:
            dists = np.zeros((X.shape[0], self.n_classes_))
            preds = self._estimator.predict(self._transformer.transform(X))
            for i in range(0, X.shape[0]):
                dists[i, self._class_dictionary[preds[i]]] = 1
            return dists
