"""General linguistic rules reviewed against the nine development exams only."""
GEOMETRY=[
 ('sliding_rod',r'glid\w* stang|stang.*skinner|metalstang.*skinner|sliding rod'),
 ('rotating_rod',r'stang.*roter|roter\w* stang|rotating rod'),
 ('capacitor',r'kondensator|capacitor'),('toroid',r'toroid'),('solenoid',r'solenoide?|spole med|lang spole'),
 ('current_sheet',r'strømplan|strømførende plan|current sheet'),('spherical_shell',r'kugleskal|spherical shell'),
 ('hollow_cylinder',r'hul\w* cylinder|cylinderskal|hollow cylinder'),('sphere',r'kugle|sphere|sfærisk område'),
 ('cylinder',r'cylinder|cylindrisk'),('slab',r'\bslab\b|planparallel\w* lag|uendelig\w* plade.*tykkelse'),
 ('disk',r'\bdisk\b|cirkulær\w* skive|flad ring.*indre radius'),('arc',r'cirkelbue|halvcirkel|\bbue\b|circular arc'),
 ('ring',r'\bring\b|strømloop|strømløkke|cirkulær\w* (?:loop|løkke|kreds)|circular loop'),
 ('wire',r'\bleder\b|\bledning\b|\bwire\b'),('line',r'linjeladning|line charge'),
 ('point_charges',r'punktladning|point charge'),('plane',r'uendelig\w* plan|infinite plane'),
 ('conductor',r'ledende metal|jordet.*plan|perfekt ledende'),('parameterized_line',r'ellipse|parametriseret|parameteriseret')]
QUALIFIERS={
 'infinite':r'\buendelig\w*\b|\binfinite\b', 'finite':r'\bendelig\w*\b|\bfinite\b',
 'solid':r'\bmassiv\w*\b|\bsolid\b','hollow':r'\bhul\w*\b|\bskal\b|\bhollow\b',
 'concentric':r'koncentrisk|concentric','parallel':r'parallel','grounded':r'jordet|grounded',
 'uniform':r'\bhomogen\w*\b|\buniform\w*\b|\bkonstant\w*\b|jævnt fordelt',
 'nonuniform':r'ikke[- ]homogen|ikke[- ]uniform|non[- ]uniform'}
WANTED=[('I_displacement',r'forskydningsstrøm|displacement current'),('curl_E',r'rotationen|curl'),('C',r'kapacitans'),('L',r'selvinduktans'),('M',r'gensidig\w* induktans|mutual inductance'),
 ('inductance',r'induktans'),('EMF',r'\bemf\b|elektromotorisk|induceret spænding'),('Phi',r'\bflux\b'),
 ('torque',r'drejningsmoment|kraftmoment|\bmomentet\b|\bmoment\b'),('F',r'\bkraft\w*\b'),('E',r'elektrisk\w* felt'),
 ('B',r'\bmagnetfelt\w*\b|magnetisk\w* felt'),('rho',r'ladningstæthed|ladningstætheden'),('Q',r'totale ladning|samlede ladning|\bladningen\b'),
 ('V',r'potential\w*'),('U',r'\benergi\w*\b'),('I',r'\bstrømmen\b|\bstrømstyrken\b'),('P',r'\beffekt\w*\b')]
