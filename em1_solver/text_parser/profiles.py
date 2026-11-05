"""Recognize advanced physical profiles without inventing missing boundary data."""
def complete_profile(out,corrections,put,question):
    messages={
        'RC':'RC-kredsløbet kræver begyndelsesladning, kobling og komponentværdier.',
        'RL':'RL-kredsløbet kræver begyndelsesstrøm, spændingskilde og kobling.',
        'ampere_maxwell':'Ampère–Maxwell kræver pladegeometri, symmetri og forsømmelige randeffekter.',
        'volume_integral':'Den endelige kilde kræver fulde rumlige integrationsgrænser og feltpunkt.'}
    question('method',messages[out.facts['model']]+' Brug Avanceret / Manuel; automatisk kompilering af denne profil er endnu ikke understøttet.',status='RED')
