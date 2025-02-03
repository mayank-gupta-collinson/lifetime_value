# Copyright 2019 The Lifetime Value Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
# Lint as: python3
"""Lifetime value metrics."""
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn import metrics


def cumulative_true(
    y_true: Sequence[float],
    y_pred: Sequence[float]
) -> np.ndarray:
  """Calculates cumulative sum of lifetime values over predicted rank.

  Arguments:
    y_true: true lifetime values.
    y_pred: predicted lifetime values.

  Returns:
    res: cumulative sum of lifetime values over predicted rank.
  """
  df = pd.DataFrame({
      'y_true': y_true,
      'y_pred': y_pred,
  }).sort_values(
      by='y_pred', ascending=False)

  return (df['y_true'].cumsum() / df['y_true'].sum()).values


def gini_from_gain(df: pd.DataFrame) -> pd.DataFrame:
  """Calculates gini coefficient over gain charts.

  Arguments:
    df: Each column contains one gain chart. First column must be ground truth.

  Returns:
    gini_result: This dataframe has two columns containing raw and normalized
                 gini coefficient.
  """
  raw = df.apply(lambda x: 2 * x.sum() / df.shape[0] - 1.)
  normalized = raw / raw[0]
  return pd.DataFrame({
      'raw': raw,
      'normalized': normalized
  })[['raw', 'normalized']]


def _normalized_rmse(y_true, y_pred):
  return np.sqrt(metrics.mean_squared_error(y_true, y_pred)) / y_true.mean()


def _normalized_mae(y_true, y_pred):
  return metrics.mean_absolute_error(y_true, y_pred) / y_true.mean()


def _aggregate_fn(df):
  return pd.Series({
      'label_mean': np.mean(df['y_true']),
      'pred_mean': np.mean(df['y_pred']),
      'normalized_rmse': _normalized_rmse(df['y_true'], df['y_pred']),
      'normalized_mae': _normalized_mae(df['y_true'], df['y_pred']),
  })


def decile_stats(
    y_true: Sequence[float],
    y_pred: Sequence[float]) -> pd.DataFrame:
  """Calculates decile level means and errors.

  The function first partites the examples into ten equal sized
  buckets based on sorted `y_pred`, and computes aggregated metrics in each
  bucket.

  Arguments:
    y_true: True labels.
    y_pred: Predicted labels.

  Returns:
    df: Bucket level statistics.
  """
  num_buckets = 10
  if y_pred is None or len(y_pred) == 0:
    raise ValueError("Input 'y_pred' is empty.")

  y_pred = pd.to_numeric(y_pred, errors='coerce')  # Ensure numeric data
  # y_pred = y_pred.dropna()  # Remove NaN values
    
  if len(y_pred) < num_buckets:
        raise ValueError("Not enough data points or unique values for the specified number of buckets.")
  # decile = pd.qcut(
  #     y_pred, q=num_buckets, labels=['%d' % i for i in range(num_buckets)],duplicates='drop')
  decile = pd.qcut(
      y_pred, q=num_buckets, labels=[str(i) for i in range(num_buckets)] ,duplicates='drop')


  df = pd.DataFrame({
      'y_true': y_true,
      'y_pred': y_pred,
      'decile': decile.astype(str),
  }).groupby('decile', group_keys=False).apply(_aggregate_fn).reset_index()

  df['decile_mape'] = np.abs(df['pred_mean'] -
                             df['label_mean']) / df['label_mean']
  return df
