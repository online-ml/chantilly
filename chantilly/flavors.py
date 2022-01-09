import abc
import typing

from river import metrics


def allowed_flavors():
    return {f().name: f() for f in [RegressionFlavor, BinaryFlavor, MultiClassFlavor]}


class Flavor(abc.ABC):

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractmethod
    def check_model(self, model: typing.Any) -> typing.Tuple[bool, str]:
        """Checks whether or not a model works for a flavor."""

    @abc.abstractmethod
    def default_metrics(self) -> typing.List[metrics.Metric]:
        """Default metrics to record globally as well as for each model."""

    @abc.abstractproperty
    def pred_func(self) -> str:
        """The name of the required prediction function."""


class RegressionFlavor(Flavor):

    @property
    def name(self):
        return 'regression'

    def check_model(self, model):
        for method in ('learn_one', 'predict_one'):
            if not hasattr(model, method):
                return False, f'The model does not implement {method}.'
        return True, None

    def default_metrics(self):
        return [metrics.MAE(), metrics.RMSE(), metrics.SMAPE()]

    @property
    def pred_func(self):
        return 'predict_one'


class BinaryFlavor(Flavor):

    @property
    def name(self):
        return 'binary'

    def check_model(self, model):
        for method in ('learn_one', 'predict_proba_one'):
            if not hasattr(model, method):
                return False, f'The model does not implement {method}.'
        return True, None

    def default_metrics(self):
        return [
            metrics.Accuracy(),
            metrics.LogLoss(),
            metrics.Precision(),
            metrics.Recall(),
            metrics.F1()
        ]

    @property
    def pred_func(self):
        return 'predict_proba_one'


class MultiClassFlavor(Flavor):

    @property
    def name(self):
        return 'multiclass'

    def check_model(self, model):
        for method in ('learn_one', 'predict_proba_one'):
            if not hasattr(model, method):
                return False, f'The model does not implement {method}.'
        return True, None

    def default_metrics(self):
        return [
            metrics.Accuracy(),
            metrics.CrossEntropy(),
            metrics.MacroPrecision(),
            metrics.MacroRecall(),
            metrics.MacroF1(),
            metrics.MicroPrecision(),
            metrics.MicroRecall(),
            metrics.MicroF1()
        ]

    @property
    def pred_func(self):
        return 'predict_proba_one'
