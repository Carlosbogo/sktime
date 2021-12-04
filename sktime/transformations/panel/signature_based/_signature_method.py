# -*- coding: utf-8 -*-

import numpy as np
from sklearn.pipeline import Pipeline

from sktime.transformations.base import _PanelToTabularTransformer
from sktime.transformations.panel.signature_based._augmentations import (
    _make_augmentation_pipeline,
)
from sktime.transformations.panel.signature_based._compute import (
    _WindowSignatureTransform,
)


class SignatureTransformer(_PanelToTabularTransformer):
    """Transformation class from the signature method.

    Follows the methodology laid out in the paper:
        "A Generalised Signature Method for Multivariate Time Series"

    Parameters
    ----------
    augmentation_list: tuple of strings, contains the augmentations to be
        applied before application of the signature transform.
    window_name: str, The name of the window transform to apply.
    window_depth: int, The depth of the dyadic window. (Active only if
        `window_name == 'dyadic'`).
    window_length: int, The length of the sliding/expanding window. (Active
        only if `window_name in ['sliding, 'expanding']`.
    window_step: int, The step of the sliding/expanding window. (Active
        only if `window_name in ['sliding, 'expanding']`.
    rescaling: str or None, The method of signature rescaling.
    sig_tfm: str, String to specify the type of signature transform. One of:
        ['signature', 'logsignature']).
    depth: int, Signature truncation depth.

    Attributes
    ----------
    signature_method: sklearn.Pipeline, A sklearn pipeline object that contains
        all the steps to extract the signature features.
    """

    _tags = {
        "X_inner_mtype": "numpy3D",
        "fit-in-transform": False,
    }

    def __init__(
        self,
        augmentation_list=("basepoint", "addtime"),
        window_name="dyadic",
        window_depth=3,
        window_length=None,
        window_step=None,
        rescaling=None,
        sig_tfm="signature",
        depth=4,
    ):
        super(SignatureTransformer, self).__init__()
        self.augmentation_list = augmentation_list
        self.window_name = window_name
        self.window_depth = window_depth
        self.window_length = window_length
        self.window_step = window_step
        self.rescaling = rescaling
        self.sig_tfm = sig_tfm
        self.depth = depth

        self.setup_feature_pipeline()

    def setup_feature_pipeline(self):
        """Set up the signature method as an sklearn pipeline."""
        augmentation_step = _make_augmentation_pipeline(self.augmentation_list)
        transform_step = _WindowSignatureTransform(
            window_name=self.window_name,
            window_depth=self.window_depth,
            window_length=self.window_length,
            window_step=self.window_step,
            sig_tfm=self.sig_tfm,
            sig_depth=self.depth,
            rescaling=self.rescaling,
        )

        # The so-called 'signature method' as defined in the reference paper
        self.signature_method = Pipeline(
            [
                ("augmentations", augmentation_step),
                ("window_and_transform", transform_step),
            ]
        )

    def _fit(self, X, y=None):
        X = np.transpose(X, [0, 2, 1])
        self.signature_method.fit(X)
        return self

    def _transform(self, X, y=None):
        X = np.transpose(X, [0, 2, 1])
        return self.signature_method.transform(X)
