#!/usr/bin/env python3
"""
Regression Analysis for Betting Models

Build simple linear and multiple regression models for betting predictions.
No external dependencies - pure Python implementation.
"""

import math
import csv
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RegressionResult:
    """Results from regression analysis"""
    coefficients: List[float]
    intercept: float
    r_squared: float
    adjusted_r_squared: float
    residual_std_error: float
    predictions: List[float]
    residuals: List[float]


class LinearRegression:
    """Simple linear regression (one predictor)"""

    def __init__(self):
        self.slope = 0
        self.intercept = 0
        self.r_squared = 0

    @staticmethod
    def mean(values: List[float]) -> float:
        """Calculate mean"""
        return sum(values) / len(values)

    @staticmethod
    def variance(values: List[float]) -> float:
        """Calculate variance"""
        avg = LinearRegression.mean(values)
        return sum((x - avg) ** 2 for x in values) / len(values)

    @staticmethod
    def covariance(x: List[float], y: List[float]) -> float:
        """Calculate covariance"""
        x_mean = LinearRegression.mean(x)
        y_mean = LinearRegression.mean(y)
        return sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x))) / len(x)

    @staticmethod
    def correlation(x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        cov = LinearRegression.covariance(x, y)
        x_std = math.sqrt(LinearRegression.variance(x))
        y_std = math.sqrt(LinearRegression.variance(y))
        return cov / (x_std * y_std)

    def fit(self, x: List[float], y: List[float]) -> 'LinearRegression':
        """
        Fit linear regression model

        Args:
            x: Predictor variable
            y: Response variable

        Returns:
            Self
        """
        if len(x) != len(y):
            raise ValueError("x and y must have same length")

        # Calculate slope and intercept
        x_mean = self.mean(x)
        y_mean = self.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(len(x)))

        self.slope = numerator / denominator
        self.intercept = y_mean - self.slope * x_mean

        # Calculate R-squared
        y_pred = [self.predict(xi) for xi in x]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(len(y)))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(len(y)))

        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return self

    def predict(self, x: float) -> float:
        """Predict y given x"""
        return self.intercept + self.slope * x

    def predict_multiple(self, x_values: List[float]) -> List[float]:
        """Predict multiple values"""
        return [self.predict(x) for x in x_values]


class MultipleRegression:
    """Multiple linear regression"""

    def __init__(self):
        self.coefficients = []
        self.intercept = 0
        self.r_squared = 0
        self.adjusted_r_squared = 0
        self.n_features = 0

    @staticmethod
    def matrix_multiply(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """Multiply two matrices"""
        rows_A = len(A)
        cols_A = len(A[0])
        cols_B = len(B[0])

        result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]

        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]

        return result

    @staticmethod
    def matrix_transpose(A: List[List[float]]) -> List[List[float]]:
        """Transpose a matrix"""
        return [[A[j][i] for j in range(len(A))] for i in range(len(A[0]))]

    @staticmethod
    def matrix_inverse_2x2(A: List[List[float]]) -> List[List[float]]:
        """Inverse of 2x2 matrix"""
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular")

        return [
            [A[1][1] / det, -A[0][1] / det],
            [-A[1][0] / det, A[0][0] / det]
        ]

    def fit(self, X: List[List[float]], y: List[float]) -> RegressionResult:
        """
        Fit multiple regression model using normal equations

        Args:
            X: Matrix of predictors (n_samples x n_features)
            y: Response variable (n_samples)

        Returns:
            RegressionResult object
        """
        n = len(y)
        self.n_features = len(X[0])

        # Add intercept column (column of 1s)
        X_with_intercept = [[1] + row for row in X]

        # For simplicity, use a gradient descent approach
        # Initialize coefficients
        theta = [0] * (self.n_features + 1)  # +1 for intercept

        # Gradient descent parameters
        learning_rate = 0.01
        iterations = 1000
        n_samples = len(X_with_intercept)

        # Normalize features for better convergence
        X_normalized = []
        means = []
        stds = []

        for j in range(len(X_with_intercept[0])):
            if j == 0:  # Don't normalize intercept column
                X_normalized.append([row[j] for row in X_with_intercept])
                means.append(0)
                stds.append(1)
            else:
                col = [row[j] for row in X_with_intercept]
                mean_val = sum(col) / len(col)
                std_val = math.sqrt(sum((x - mean_val) ** 2 for x in col) / len(col))
                std_val = std_val if std_val > 0 else 1  # Avoid division by zero

                normalized_col = [(x - mean_val) / std_val for x in col]
                X_normalized.append(normalized_col)
                means.append(mean_val)
                stds.append(std_val)

        # Transpose for easier access
        X_norm_T = X_normalized

        # Gradient descent
        for _ in range(iterations):
            # Calculate predictions
            predictions = []
            for i in range(n_samples):
                pred = sum(theta[j] * X_norm_T[j][i] for j in range(len(theta)))
                predictions.append(pred)

            # Calculate gradients
            gradients = []
            for j in range(len(theta)):
                gradient = sum((predictions[i] - y[i]) * X_norm_T[j][i] for i in range(n_samples))
                gradient /= n_samples
                gradients.append(gradient)

            # Update theta
            theta = [theta[j] - learning_rate * gradients[j] for j in range(len(theta))]

        # Denormalize coefficients
        self.intercept = theta[0]
        for j in range(1, len(theta)):
            self.intercept -= theta[j] * means[j] / stds[j]

        self.coefficients = [theta[j] / stds[j] for j in range(1, len(theta))]

        # Calculate predictions with original features
        predictions = [self.predict(X[i]) for i in range(n)]

        # Calculate R-squared
        y_mean = sum(y) / len(y)
        ss_res = sum((y[i] - predictions[i]) ** 2 for i in range(n))
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)

        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Adjusted R-squared
        n_params = len(self.coefficients) + 1
        self.adjusted_r_squared = 1 - ((1 - self.r_squared) * (n - 1) / (n - n_params))

        # Residual standard error
        residuals = [y[i] - predictions[i] for i in range(n)]
        residual_std_error = math.sqrt(sum(r ** 2 for r in residuals) / (n - n_params))

        return RegressionResult(
            coefficients=self.coefficients,
            intercept=self.intercept,
            r_squared=self.r_squared,
            adjusted_r_squared=self.adjusted_r_squared,
            residual_std_error=residual_std_error,
            predictions=predictions,
            residuals=residuals
        )

    def predict(self, x: List[float]) -> float:
        """
        Predict y given feature vector x

        Args:
            x: Feature vector

        Returns:
            Predicted value
        """
        return self.intercept + sum(self.coefficients[i] * x[i] for i in range(len(x)))

    def predict_multiple(self, X: List[List[float]]) -> List[float]:
        """Predict multiple samples"""
        return [self.predict(x) for x in X]


def print_regression_summary(result: RegressionResult, feature_names: Optional[List[str]] = None):
    """Print regression results"""
    print(f"\n{'='*70}")
    print(f"REGRESSION ANALYSIS RESULTS")
    print(f"{'='*70}")

    print(f"\nModel Performance:")
    print(f"  R-squared: {result.r_squared:.4f}")
    print(f"  Adjusted R-squared: {result.adjusted_r_squared:.4f}")
    print(f"  Residual Std Error: {result.residual_std_error:.4f}")

    print(f"\nCoefficients:")
    print(f"  Intercept: {result.intercept:.4f}")

    if feature_names is None:
        feature_names = [f"X{i+1}" for i in range(len(result.coefficients))]

    for i, coef in enumerate(result.coefficients):
        print(f"  {feature_names[i]}: {coef:.4f}")

    print(f"\n{'='*70}")


def load_data_from_csv(filename: str) -> Tuple[List[List[float]], List[float], List[str]]:
    """
    Load data from CSV file

    CSV format: feature1,feature2,...,target

    Returns:
        (X, y, column_names)
    """
    X = []
    y = []
    column_names = []

    with open(filename, 'r') as f:
        reader = csv.reader(f)
        column_names = next(reader)  # Header row

        for row in reader:
            values = [float(v) for v in row]
            X.append(values[:-1])  # All but last column
            y.append(values[-1])    # Last column is target

    feature_names = column_names[:-1]
    target_name = column_names[-1]

    return X, y, feature_names


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Regression Analysis for Betting Models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple linear regression (manual data)
  %(prog)s --simple --x 1 2 3 4 5 --y 2 4 5 4 5

  # Multiple regression from CSV
  %(prog)s --csv data.csv

  # Predict new values
  %(prog)s --csv data.csv --predict 3.5 2.1 1.8

CSV Format:
  feature1,feature2,...,featureN,target
  1.0,2.0,3.0,5.5
  2.0,3.0,4.0,7.2
  ...

Use Cases:
  - Predict team totals from offensive/defensive stats
  - Forecast player props from historical averages
  - Model win probability from power ratings
        """
    )

    parser.add_argument('--simple', action='store_true',
                       help='Simple linear regression')
    parser.add_argument('--csv', type=str,
                       help='CSV file with training data')
    parser.add_argument('--x', nargs='+', type=float,
                       help='X values for simple regression')
    parser.add_argument('--y', nargs='+', type=float,
                       help='Y values for simple regression')
    parser.add_argument('--predict', nargs='+', type=float,
                       help='Predict for new feature values')

    args = parser.parse_args()

    if args.simple:
        if not args.x or not args.y:
            parser.error("--simple requires --x and --y")

        if len(args.x) != len(args.y):
            parser.error("--x and --y must have same length")

        # Fit model
        model = LinearRegression()
        model.fit(args.x, args.y)

        print(f"\n{'='*70}")
        print(f"SIMPLE LINEAR REGRESSION")
        print(f"{'='*70}")

        print(f"\nModel: y = {model.intercept:.4f} + {model.slope:.4f} * x")
        print(f"R-squared: {model.r_squared:.4f}")

        # Correlation
        corr = LinearRegression.correlation(args.x, args.y)
        print(f"Correlation: {corr:.4f}")

        # Predictions
        predictions = model.predict_multiple(args.x)
        print(f"\nPredictions:")
        print(f"{'X':<10} {'Actual':<10} {'Predicted':<12} {'Residual':<12}")
        print(f"{'-'*50}")
        for i in range(len(args.x)):
            residual = args.y[i] - predictions[i]
            print(f"{args.x[i]:<10.2f} {args.y[i]:<10.2f} {predictions[i]:<12.2f} {residual:<12.2f}")

        if args.predict:
            print(f"\nNew Predictions:")
            for x_val in args.predict:
                pred = model.predict(x_val)
                print(f"  x = {x_val:.2f} → y = {pred:.2f}")

        print(f"\n{'='*70}")

    elif args.csv:
        X, y, feature_names = load_data_from_csv(args.csv)

        if len(X[0]) == 1:
            # Simple regression
            x_vals = [row[0] for row in X]
            model = LinearRegression()
            model.fit(x_vals, y)

            print(f"\n{'='*70}")
            print(f"SIMPLE LINEAR REGRESSION (from CSV)")
            print(f"{'='*70}")

            print(f"\nModel: y = {model.intercept:.4f} + {model.slope:.4f} * {feature_names[0]}")
            print(f"R-squared: {model.r_squared:.4f}")

            if args.predict:
                pred = model.predict(args.predict[0])
                print(f"\nPrediction: {pred:.4f}")

            print(f"\n{'='*70}")

        else:
            # Multiple regression
            model = MultipleRegression()
            result = model.fit(X, y)

            print_regression_summary(result, feature_names)

            if args.predict:
                if len(args.predict) != len(feature_names):
                    print(f"\nError: Need {len(feature_names)} features for prediction")
                else:
                    pred = model.predict(args.predict)
                    print(f"\nPrediction: {pred:.4f}")
                    print(f"{'='*70}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
