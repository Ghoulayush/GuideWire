import importlib, traceback

try:
    m = importlib.import_module('app.services.premium_calculator')
    print('MODULE FILE:', getattr(m, '__file__', None))
    print('MODULE KEYS:', list(m.__dict__.keys()))
    print('HAS premium_calculator=', hasattr(m, 'premium_calculator'))
    if hasattr(m, 'premium_calculator'):
        print('premium_calculator repr:', repr(m.premium_calculator))
except Exception as e:
    print('ERR', e)
    traceback.print_exc()
