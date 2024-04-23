import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import RFECV
from sklearn.ensemble import RandomForestClassifier
import joblib
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Load dataset
def load_dataset(file_path):
    data = pd.read_csv(file_path)
    return data

# Preprocess data
def preprocess_data(data):
    # Separate features and target variable
    X = data.drop(columns=['target_column'])
    y = data['target_column']
    
    # Define preprocessing steps for numeric and categorical features
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object']).columns.tolist()
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))])
    
    # Apply transformations to respective feature types
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)])
    
    # Return preprocessed data
    return preprocessor.fit_transform(X)

# Train predictive maintenance model
def train_predictive_maintenance_model(X_train, X_test, y_train, y_test):
    # Define base classifier
    base_classifier = RandomForestClassifier(random_state=42)
    
    # Perform Recursive Feature Elimination with Cross-Validation (RFECV)
    selector = RFECV(estimator=base_classifier, step=1, cv=StratifiedKFold(5), scoring='accuracy')
    selector = selector.fit(X_train, y_train)
    
    # Prune less impactful features
    X_train_selected = selector.transform(X_train)
    X_test_selected = selector.transform(X_test)
    
    # Define hyperparameter grid for RandomizedSearchCV
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'bootstrap': [True, False]
    }
    
    # Randomized search for hyperparameter optimization
    rf_random = RandomizedSearchCV(estimator=base_classifier, param_distributions=param_grid, n_iter=100, cv=3, verbose=2, random_state=42, n_jobs=-1)
    rf_random.fit(X_train_selected, y_train)
    
    # Retrieve best parameters
    best_params = rf_random.best_params_
    
    # Train classifier with best parameters
    classifier = RandomForestClassifier(**best_params, random_state=42)
    classifier.fit(X_train_selected, y_train)
    
    # Make predictions
    y_pred = classifier.predict(X_test_selected)
    
    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    print("Accuracy:", accuracy)
    print("Classification Report:")
    print(report)
    
    # Save model
    joblib.dump(classifier, 'predictive_maintenance_model.pkl')
    
    # Plot feature importance
    feature_importance = selector.estimator_.feature_importances_
    plt.bar(range(len(feature_importance)), feature_importance)
    plt.show()

if __name__ == "__main__":
    # Load dataset
    data = load_dataset('data.csv')
    
    # Preprocess data
    X = preprocess_data(data)
    y = data['target_column']
    
    # Split data into training and testing sets with stratified sampling
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train predictive maintenance model
    train_predictive_maintenance_model(X_train, X_test, y_train, y_test)
