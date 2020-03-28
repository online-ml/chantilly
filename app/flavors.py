import abc
import typing

from creme import metrics


def allowed_flavors():
    return [f().name for f in [RegressionFlavor]]


class Flavor(abc.ABC):

    @abc.abstractproperty
    def name(self): pass

    @abc.abstractmethod
    def validate_model(self, model: typing.Any) -> typing.Tuple[bool, str]:
        """Checks whether or not a model works for a flavor."""

    @abc.abstractmethod
    def default_metrics(self) -> typing.List[metrics.Metric]:
        """Default metrics to record globally as well as for each model."""


class RegressionFlavor(Flavor):

    @property
    def name(self):
        return 'regression'

    def validate_model(self, model):
        if not hasattr(model, 'fit_one'):
            return False, 'The model does not implement fit_one.'
        if not hasattr(model, 'predict_one'):
            return False, 'The model does not implement predict_one.'
        return True, None

    def default_metrics(self):
        return [metrics.MAE(), metrics.RMSE(), metrics.SMAPE()]



# if isinstance(model, creme.base.BinaryClassifier):
#     shelf['metrics'] = [
#         creme.metrics.Accuracy(),
#         creme.metrics.LogLoss(),
#         creme.metrics.Precision(),
#         creme.metrics.Recall(),
#         creme.metrics.F1()
#     ]
# elif isinstance(model, creme.base.MultiClassifier):
#     shelf['metrics'] = [
#         creme.metrics.Accuracy(),
#         creme.metrics.CrossEntropy(),
#         creme.metrics.MacroPrecision(),
#         creme.metrics.MacroRecall(),
#         creme.metrics.MacroF1(),
#         creme.metrics.MicroPrecision(),
#         creme.metrics.MicroRecall(),
#         creme.metrics.MicroF1()
#     ]
# elif isinstance(model, creme.base.Regressor):
#     shelf['metrics'] = [
#         creme.metrics.MAE(),
#         creme.metrics.RMSE(),
#         creme.metrics.SMAPE()
#     ]
# else:
#     raise ValueError('Unknown model type')
