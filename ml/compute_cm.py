import joblib
import pandas as pd
from ml.preprocessing import preprocess_text
from sklearn.metrics import confusion_matrix


def compute_category_cm():
    tfidf = joblib.load('ml/models/tfidf.pkl')
    cat = joblib.load('ml/models/category.pkl')
    df = pd.read_csv('ml/dataset/test_hostel.csv')
    X = df['complaint'].astype(str).apply(preprocess_text)
    X_t = tfidf.transform(X)
    y_true = df['hostel_category'].values
    y_pred = cat.predict(X_t)
    labels = sorted(set(y_true))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return labels, cm, y_true, y_pred


def compute_priority_cm():
    tfidf = joblib.load('ml/models/tfidf.pkl')
    prio = joblib.load('ml/models/priority.pkl')
    df = pd.read_csv('ml/dataset/test_hostel.csv')
    X = df['complaint'].astype(str).apply(preprocess_text)
    X_t = tfidf.transform(X)
    y_true = df['priority'].values
    y_pred = prio.predict(X_t)
    labels = sorted(set(y_true))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return labels, cm, y_true, y_pred


if __name__ == '__main__':
    labels_cat, cm_cat, y_true_cat, y_pred_cat = compute_category_cm()
    print('Category labels:', labels_cat)
    print('Category confusion matrix:\n', cm_cat)

    # Find most common errors (actual->predicted counts excluding diagonal)
    import numpy as np
    errors = []
    for i, a in enumerate(labels_cat):
        for j, p in enumerate(labels_cat):
            if i != j and cm_cat[i, j] > 0:
                errors.append(((a, p), int(cm_cat[i, j])))
    errors.sort(key=lambda x: x[1], reverse=True)
    print('Most common category errors (actual->predicted, count):', errors[:10])

    labels_prio, cm_prio, y_true_prio, y_pred_prio = compute_priority_cm()
    print('\nPriority labels:', labels_prio)
    print('Priority confusion matrix:\n', cm_prio)

    errors_pr = []
    for i, a in enumerate(labels_prio):
        for j, p in enumerate(labels_prio):
            if i != j and cm_prio[i, j] > 0:
                errors_pr.append(((a, p), int(cm_prio[i, j])))
    errors_pr.sort(key=lambda x: x[1], reverse=True)
    print('Most common priority errors (actual->predicted, count):', errors_pr[:10])
