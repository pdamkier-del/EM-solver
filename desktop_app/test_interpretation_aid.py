from interpretation_aid import text_corrections

def check(text, expected):
    corrections,evidence=text_corrections(text)
    assert corrections==expected, (text,corrections,expected)
    assert bool(evidence)==bool(expected)

check('Den radiale koordinat er s. En cylinder har radius R.',{'coordinate':'s'})
check('hvor s er den radiale afstand fra cylinderens akse.',{'coordinate':'s'})
check('s er afstanden fra cylinderens akse.',{'coordinate':'s'})
check('En kugle har radius R, hvor r er den radiale koordinat.',{'coordinate':'r'})
check('En cylinder med E(s) og radius R.',{})
check('En cylinder med radius R, og s betegner en tid.',{})
check('Den radiale koordinat er s, men den radiale koordinat er r.',{})
assert text_corrections('Den radiale koordinat er s',{'coordinate':'r'})==({}, {})
print('8 tests af eksplicit koordinatgenkendelse OK')
