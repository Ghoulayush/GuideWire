"""Train the fraud ensemble and write the model to models/"""
from app.services.fraud.ensemble import FraudEnsemble


def main():
    fe = FraudEnsemble(model_path='models/fraud_ensemble.pkl')
    print('Training fraud ensemble (synthetic data, CPU-friendly)...')
    report = fe.train_on_synthetic(n_samples=5000, save=True)
    print('Training complete:', report)


if __name__ == '__main__':
    main()
