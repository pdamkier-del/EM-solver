"""Method proposals use supplied quantities and explicit symmetry, never keywords alone."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Proposal:
    family:str
    domain:str
    reason:str
    requirements:str

def propose(given,wanted,geometry='',symmetry_confirmed=False,domain='Ved ikke'):
    given,wanted=set(given),set(wanted);out=[]
    def add(f,d,r,needs):
        if domain in ('Ved ikke',d):out.append(Proposal(f,d,r,needs))
    if 'point charges' in given and wanted&{'E','V','force','energy'}:add('point_charges','EV','Diskrete ladninger summeres vektorielt.','Ladninger, positioner og feltpunkt.')
    if 'V' in given and 'E' in wanted:add('field_calculus','EV','E=-grad(V) er den direkte relation.','Potentialfunktion og koordinatsystem.')
    if 'E' in given and 'rho' in wanted:add('field_calculus','EV','Gauss’ differentiallov giver ladningstætheden.','Alle feltkomponenter og koordinatsystem.')
    if 'E' in given and 'V' in wanted:add('potential_from_field','EV','Potentialforskellen er minus linjeintegralet.','Orienteret vej og begge referencepunkter.')
    if given&{'rho','sigma','lambda'} and wanted&{'E','V'}:
        if symmetry_confirmed and geometry in ('Uendelig cylinder','Kuglesymmetri','Uendeligt plan'):
            add('gauss_radial','EV','Den bekræftede symmetri tillader en Gauss-flade med konstant normalfelt.','Tæthed, radiale regioner og permittiviteter.')
        add('coulomb_integral','EV','Direkte kildeintegration kræver ingen Gauss-symmetri.','Kildeparameterisering, målpunkt og integrationsgrænser.')
    if 'A' in given and 'B' in wanted:add('field_calculus','BA','B=curl(A) beregnes i den angivne basis.','Tre A-komponenter og koordinatsystem.')
    if given&{'J','I'} and 'B' in wanted:
        if symmetry_confirmed and geometry=='Uendelig cylinder':add('ampere','BA','Aksial strøm og bekræftet uendelig cylindersymmetri giver en cirkulær Ampère-kurve.','J(s), radier og strømretning.')
        add('biot_savart','BA','Orienterede ledningselementer kan integreres direkte.','Ledningskurve, strøm og feltpunkt.')
    if given&{'B','flux'} and wanted&{'EMF','current','power','energy'}:add('faraday','DYN','Integrer flux og differentier hele dens tidsafhængighed.','Fladenormal/geometri, tidslov, vindingstal; R og negligerbar selvinduktans for strøm.')
    if 'E' in given and 'B' in wanted:add('ampere_maxwell','DYN','Et tidsafhængigt elektrisk felt kan skabe forskydningsstrøm.','Tidslov, cirkulær symmetri og pladegeometri skal verificeres.')
    return out
