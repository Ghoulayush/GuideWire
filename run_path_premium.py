import runpy, pprint

d = runpy.run_path('app/services/premium_calculator.py')
print('run_path keys sample=', list(d.keys())[:80])
if 'premium_calculator' in d:
    print('premium_calculator found in run_path')
    pprint.pprint(d['premium_calculator'].__class__.__name__)
else:
    print('premium_calculator NOT found in run_path')
