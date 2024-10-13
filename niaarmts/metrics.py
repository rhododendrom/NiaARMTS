import pandas as pd
import numpy as np

def calculate_support(df, antecedents, consequents, start=0, end=0, use_interval=False):
    """
    Calculate the support for the given list of antecedents and consequents within the specified time range or interval range.

    Args:
        df (pd.DataFrame): The dataset containing the transactions.
        antecedents (list): A list of dictionaries defining the antecedent conditions.
        consequents (list): A list of dictionaries defining the consequent conditions.
        start (int or datetime): The start of the interval (if use_interval is True) or timestamp range.
        end (int or datetime): The end of the interval (if use_interval is True) or timestamp range.
        use_interval (bool): Whether to filter by 'interval' (True) or 'timestamp' (False) for time-based filtering.

    Returns:
        float: The support value, which is the ratio of transactions matching both antecedents and consequents
        to the total transactions in the filtered range. If no transactions exist, returns 0.
    """
    if use_interval:
        df_filtered = df[(df['interval'] >= start) & (df['interval'] <= end)]
    else:
        df_filtered = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]

    filtered = len(df_filtered)

    # Apply each antecedent condition
    for antecedent in antecedents:
        if antecedent['type'] == 'Categorical':
            df_filtered = df_filtered[df_filtered[antecedent['feature']] == antecedent['category']]
        elif antecedent['type'] == 'Numerical':
            df_filtered = df_filtered[
                (df_filtered[antecedent['feature']] >= antecedent['border1']) &
                (df_filtered[antecedent['feature']] <= antecedent['border2'])
            ]

    # Apply each consequent condition
    for consequent in consequents:
        if consequent['type'] == 'Categorical':
            df_filtered = df_filtered[df_filtered[consequent['feature']] == consequent['category']]
        elif consequent['type'] == 'Numerical':
            df_filtered = df_filtered[
                (df_filtered[consequent['feature']] >= consequent['border1']) &
                (df_filtered[consequent['feature']] <= consequent['border2'])
            ]

    # Calculate support: the ratio of rows matching both antecedents and consequents to total filtered rows
    return len(df_filtered) / filtered if len(df) > 0 else 0


def calculate_confidence(df, antecedents, consequents, start, end, use_interval=False):
    """
    Calculate the confidence for the given list of antecedents and consequents within the specified time range or interval range.

    Args:
        df (pd.DataFrame): The dataset containing the transactions.
        antecedents (list): A list of dictionaries defining the antecedent conditions.
        consequents (list): A list of dictionaries defining the consequent conditions.
        start (int or datetime): The start of the interval (if use_interval is True) or timestamp range.
        end (int or datetime): The end of the interval (if use_interval is True) or timestamp range.
        use_interval (bool): Whether to filter by 'interval' (True) or 'timestamp' (False) for time-based filtering.

    Returns:
        float: The confidence value, which is the ratio of rows matching both antecedents and consequents
        to the rows matching antecedents. If no antecedent-matching rows exist, returns 0.
    """
    if use_interval:
        df_filtered = df[(df['interval'] >= start) & (df['interval'] <= end)]
    else:
        df_filtered = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]

    filtered = len(df_filtered)

    # Apply each antecedent condition
    for antecedent in antecedents:
        if antecedent['type'] == 'Categorical':
            df_filtered = df_filtered[df_filtered[antecedent['feature']] == antecedent['category']]
        elif antecedent['type'] == 'Numerical':
            if 'border1' in antecedent and 'border2' in antecedent:
                df_filtered = df_filtered[
                    (df_filtered[antecedent['feature']] >= antecedent['border1']) &
                    (df_filtered[antecedent['feature']] <= antecedent['border2'])
                ]
            else:
                raise ValueError("Numerical antecedent must have 'border1' and 'border2'")

    antecedent_support = df_filtered.copy()

    # Apply consequent conditions to the antecedent-supporting rows
    for consequent in consequents:
        if consequent['type'] == 'Categorical':
            antecedent_support = antecedent_support[antecedent_support[consequent['feature']] == consequent['category']]
        elif consequent['type'] == 'Numerical':
            if 'border1' in consequent and 'border2' in consequent:
                antecedent_support = antecedent_support[
                    (antecedent_support[consequent['feature']] >= consequent['border1']) &
                    (antecedent_support[consequent['feature']] <= consequent['border2'])
                ]
            else:
                raise ValueError("Numerical consequent must have 'border1' and 'border2'")

    antecedent_count = len(df_filtered)
    consequent_count = len(antecedent_support)

    # Calculate confidence: the ratio of rows that match both antecedents and consequents to the rows matching antecedents
    return consequent_count / antecedent_count if antecedent_count > 0 else 0.0


def calculate_inclusion_metric(features, antecedents, consequents):
    """
    Calculate the inclusion metric, which measures how many attributes appear in both the antecedent and consequent
    relative to the total number of features in the dataset.

    Args:
        features (dict): A dictionary of feature metadata for the dataset.
        antecedents (list): A list of dictionaries defining the antecedent conditions.
        consequents (list): A list of dictionaries defining the consequent conditions.

    Returns:
        float: The inclusion metric value, normalized between 0 and 1.
    """
    all_dataset_features = len(features)
    antecedent_features = {feature['feature'] for feature in antecedents}
    consequent_features = {feature['feature'] for feature in consequents}

    common_features = len(consequent_features) + len(antecedent_features)

    if common_features == 0:
        return 0.0

    # Calculate inclusion metric normalized by total features
    inclusion_metric = common_features / all_dataset_features

    return inclusion_metric


def calculate_amplitude_metric(features, antecedents, consequents):
    """
    Calculate the amplitude metric for the given rule, based on the ranges of numerical attributes in the antecedents
    and consequents. The amplitude metric rewards smaller ranges, indicating tighter intervals for numerical conditions.

    Args:
        features (dict): A dictionary of feature metadata for the dataset.
        antecedents (list): A list of dictionaries defining the antecedent conditions.
        consequents (list): A list of dictionaries defining the consequent conditions.

    Returns:
        float: The amplitude metric value, normalized between 0 and 1. A higher value indicates tighter numerical ranges
        in the antecedents and consequents.
    """
    total_range = 0.0
    num_numerical_attributes = 0

    # Combine antecedents and consequents
    rule_parts = antecedents + consequents

    for feature in rule_parts:
        if feature['type'] == 'Numerical':
            border1 = feature['border1']
            border2 = feature['border2']

            # Retrieve the original feature min and max from the dataset metadata
            feature_min = features[feature['feature']]['min']
            feature_max = features[feature['feature']]['max']

            # Calculate the normalized range
            if feature_max != feature_min:
                normalized_range = (border2 - border1) / (feature_max - feature_min)
            else:
                normalized_range = 0.0  # If no variation in the feature, set range to 0

            total_range += normalized_range
            num_numerical_attributes += 1

    # If there are no numerical attributes, return 0
    if num_numerical_attributes == 0:
        return 0.0

    # Amplitude metric is 1 - (average normalized range), meaning smaller ranges are preferred
    amplitude_metric = 1 - (total_range / num_numerical_attributes)

    return amplitude_metric


def calculate_fitness(supp, conf, incl, alpha=1.0, beta=1.0, delta=1.0):
    """
    Calculate the fitness score of a rule using the weighted sum of support, confidence, and inclusion.

    The fitness function is used to evaluate how good a particular rule is, based on its support, confidence,
    and inclusion metrics. The function allows weighting of each metric through the alpha, beta, and delta parameters.

    Args:
        supp (float): The support value of the rule.
        conf (float): The confidence value of the rule.
        incl (float): The inclusion value of the rule.
        alpha (float): Weight for the support metric.
        beta (float): Weight for the confidence metric.
        delta (float): Weight for the inclusion metric.

    Returns:
        float: The fitness score, normalized between 0 and 1.
    """
    return ((alpha * supp) + (beta * conf) + (delta * incl)) / 3
