import importlib, traceback

modules = [
    'app.services.ml_risk',
    'app.services.premium_calculator',
]

for mod in modules:
    try:
        m = importlib.import_module(mod)
        print(mod, 'loaded. module dict keys sample=', list(m.__dict__.keys())[:40])
        # Explicitly show whether the expected symbols exist
        print('  has_risk_model=', hasattr(m, 'risk_model'))
        print('  has_premium_calculator=', hasattr(m, 'premium_calculator'))
    except Exception as e:
        print('FAILED to import', mod, e)
        traceback.print_exc()
