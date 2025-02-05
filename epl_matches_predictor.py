# -*- coding: utf-8 -*-
"""EPL-Matches-Predictor.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1rE7seLkQv5ebxWsFX1EfabbVvy_kHD2t
"""

import pandas as pd

matches = pd.read_csv('matches.csv', index_col=0)

matches["date"] = pd.to_datetime(matches["date"])

matches["venue_code"] = matches["venue"].astype("category").cat.codes

matches["hour_code"] = matches["time"].str.replace(":.+", "", regex=True).astype("int")

matches["day_code"] = matches["date"].dt.dayofweek

matches["opp_code"] = matches["opponent"].astype("category").cat.codes

matches["target"] = (matches["result"] == "W").astype("int")

from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

train = matches[matches["date"] < '2022-01-01']

test = matches[matches["date"] >= '2022-01-01']

predictors = ["venue_code", "hour_code", "day_code", "opp_code"]

rf.fit(train[predictors], train["target"])

preds = rf.predict(test[predictors])

from sklearn.metrics import accuracy_score

acc = accuracy_score(test["target"], preds)

combined = pd.DataFrame(dict(actual =  test["target"], prediction = preds))

pd.crosstab(combined["actual"], combined["prediction"])

from sklearn.metrics import precision_score

precision = precision_score(test["target"], preds)

grouped_matches = matches.groupby("team")

group = grouped_matches.get_group("Manchester United").sort_values("date")

def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3, closed='left').mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
new_cols = [f"{c}_rolling" for c in cols]

rolling_averages(group, cols, new_cols)

matches_rolling = matches.groupby("team").apply(lambda x: rolling_averages(x, cols, new_cols))

matches_rolling = matches_rolling.droplevel('team')

matches_rolling.index = range(matches_rolling.shape[0])

matches_rolling

def make_predictions(data, predictors): ## making the predictions
    train = data[data["date"] < '2022-01-01']
    test = data[data["date"] > '2022-01-01']
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors]) ##making prediction
    combined = pd.DataFrame(dict(actual=test["target"], prediction=preds), index=test.index)
    precision = precision_score(test["target"], preds)
    return combined, precision ## returning the values for the prediction

combined, precision = make_predictions(matches_rolling, predictors + new_cols)

combined

precision

combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

combined

class MissingDict(dict):
   __missing__ = lambda self, key: key

map_values= {
    "Manchester United": "Manchester Utd",
    "West Ham United": "West Ham",
    "Newcastle United": "Newcastle Utd",
    "Tottenham Hotspur": "Tottenham",
    "Wolverhampton Wanderers": "Wolves",
    "Brighton & Hove Albion": "Brighton"
}

mapping = MissingDict(**map_values)

combined["new_teams"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on=["date","new_teams"] , right_on=["date", "opponent"]) #combining both home and away matched for both teams

merged.to_csv("matches_predicted.csv")

