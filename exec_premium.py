g = {}
exec(open('app/services/premium_calculator.py', 'r', encoding='utf-8').read(), g)
print('exec keys sample=', list(g.keys())[:80])
print('premium_calculator in exec?', 'premium_calculator' in g)
if 'premium_calculator' in g:
    print('repr:', repr(g['premium_calculator']))
