import numpy as np
import pandas as pd

from sklearn.linear_model.base import LinearModel

import pytest

from xsd.pointwise_models.utils import LinearTrendTransformer, QuantileMapper
from xsd.pointwise_models import (
    BcsdPrecipitation,
    BcsdTemperature,
    PureAnalog,
    AnalogRegression,
    ZScoreRegressor
)


def test_linear_trend_roundtrip():
    # TODO: there is probably a better analytic test here
    n = 100
    trend = 1
    yint = 15

    trendline = trend * np.arange(n) + yint
    noise = np.sin(np.linspace(-10 * np.pi, 10 * np.pi, n)) * 10
    data = trendline + noise

    ltt = LinearTrendTransformer()

    # remove trend
    d_no_trend = ltt.fit_transform(data)

    # assert detrended data is equal to noise
    np.testing.assert_almost_equal(d_no_trend, noise, decimal=0)
    # assert linear coef is equal to trend
    np.testing.assert_almost_equal(ltt.lr_model_.coef_, trend, decimal=0)
    # assert roundtrip
    np.testing.assert_array_equal(ltt.inverse_transform(d_no_trend), data)


def test_quantile_mapper():
    n = 100
    expected = np.sin(np.linspace(-10 * np.pi, 10 * np.pi, n)) * 10
    with_bias = expected + 2

    mapper = QuantileMapper()
    mapper.fit(expected)
    actual = mapper.transform(with_bias)
    np.testing.assert_almost_equal(actual.squeeze(), expected)


@pytest.mark.xfail(reason="Need 3 part QM routine to handle bias removal")
def test_quantile_mapper_detrend():
    n = 100
    trend = 1
    yint = 15

    trendline = trend * np.arange(n) + yint
    base = np.sin(np.linspace(-10 * np.pi, 10 * np.pi, n)) * 10
    expected = base + trendline

    with_bias = expected + 2

    mapper = QuantileMapper(detrend=True)
    mapper.fit(base)
    actual = mapper.transform(with_bias)
    np.testing.assert_almost_equal(actual.squeeze(), expected)


@pytest.mark.parametrize(
    "model_cls", [BcsdPrecipitation, BcsdTemperature, PureAnalog, AnalogRegression, ZScoreRegressor]
)
def test_linear_model(model_cls):

    n = 100
    index = pd.date_range("2019-01-01", periods=n)

    X = pd.DataFrame(
        {"foo": np.sin(np.linspace(-10 * np.pi, 10 * np.pi, n)) * 10}, index=index
    )
    y = X + 2

    model = model_cls()
    model.fit(X, y)
    model.predict(X)
    assert isinstance(model, LinearModel)


def test_zscore_scale():
    time = pd.date_range(start='2018-01-01', end='2020-01-01')
    data_X = np.linspace(0,1,len(time))
    data_y = data_X * 2

    X = xr.DataArray(data_X, name='foo', dims=['index'], coords = {'index': time}).to_dataframe()
    y = xr.DataArray(data_y, name='foo', dims=['index'], coords = {'index': time}).to_dataframe()


    data_scale_expected = [2 for i in np.zeros(364)]
    scale_expected = xr.DataArray(data_scale_expected, name='foo', dims=['day'], coords = {'day': np.arange(1,365)}).to_dataframe()

    zscore = ZScoreRegressor()
    zscore.fit(X, y)

    np.testing.assert_allclose(zscore.scale, scale_expected)

def test_zscore_shift():
    time = pd.date_range(start='2018-01-01', end='2020-01-01')
    data_X = np.ones(len(time))
    data_y = np.zeros(len(time))

    X = xr.DataArray(data_X, name='foo', dims=['index'], coords = {'index': time}).to_dataframe()
    y = xr.DataArray(data_y, name='foo', dims=['index'], coords = {'index': time}).to_dataframe()

    data_shift_expected = [-1 for i in np.zeros(364)]
    shift_expected = xr.DataArray(data_shift_expected, name='foo', dims=['day'], coords = {'day': np.arange(1,365)}).to_dataframe()

    zscore = ZScoreRegressor()
    zscore.fit(X, y)

    np.testing.assert_allclose(zscore.shift, shift_expected)