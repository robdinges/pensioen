"""Vertaal de pensioenraming naar drie scenario's; fiscale engine blijft leidend."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from pensioen.calculations.actuariele_schatting import grondslagen, maand_plus, schat_regeling
from pensioen.models.opbouw_simulatie import ActuarieleKeuze
from pensioen.models.component import BedragType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario

NAMEN = ['Direct pensioen bij stoppen', 'Wachten zonder doorbetalen', 'Doorbetalen en later pensioen']


def bouw_actuariele_scenarios(basis: Scenario, persoon: Persoon, keuze: ActuarieleKeuze,
                             jaar_van: int, jaar_tot: int) -> tuple[list[Scenario], dict[str, Any]]:
    arbeid=[c for c in basis.componenten if c.persoon==keuze.persoon and c.categorie==CategorieComponent.ARBEIDSINKOMEN and (c.bedrag>0 or c.waarde_periodes)]
    if not arbeid or any(c.einddatum is None for c in arbeid):
        raise ValueError('Vul in je scenario bij alle loonposten van deze persoon een einddatum in. Daaruit halen we de stopdatum.')
    if any(c.waarde_periodes for c in arbeid):
        raise ValueError('Gebruik voor deze raming loonposten zonder waardeperiodes, met een expliciete einddatum.')
    pensioen_indices={i for i,c in enumerate(basis.componenten) if c.persoon==keuze.persoon and c.categorie==CategorieComponent.PENSIOEN_INKOMEN}
    if not set(keuze.reeds_opgebouwde_posten).issubset(pensioen_indices):
        raise ValueError('De geselecteerde reeds opgebouwde pensioenpost hoort niet bij deze persoon of bestaat niet meer.')
    laatste=max(c.einddatum for c in arbeid if c.einddatum)
    stop=maand_plus(date(laatste.year,laatste.month,1),1)
    if not jaar_van<=stop.year<=jaar_tot:
        raise ValueError('De eerste maand na stoppen moet binnen de berekeningsperiode liggen.')
    g=grondslagen()
    rente=keuze.rekenrente_pct if keuze.rekenrente_pct is not None else Decimal(g['rekenrente_pct'])
    startleeftijd=keuze.startleeftijd_opbouw or g['startleeftijd_opbouw']
    opslag=keuze.premie_kostenopslag_pct if keuze.premie_kostenopslag_pct is not None else Decimal(g['premie_kostenopslag_pct'])
    rentes={rente,*(Decimal(r) for r in g['gevoeligheid_rentes_pct'])}
    scenarios=[basis.model_copy(deep=True) for _ in NAMEN]
    for scenario,naam in zip(scenarios,NAMEN):
        scenario.naam=naam
        scenario.parent_naam=None
        scenario.overrides={}
    regels=[]
    overgeslagen=[]
    for index,post in enumerate(basis.componenten):
        if post.persoon!=keuze.persoon or post.categorie!=CategorieComponent.PENSIOEN_INKOMEN:
            continue
        if not post.begindatum:
            raise ValueError(f'Vul bij pensioenpost {post.omschrijving} de oorspronkelijke ingangsdatum in.')
        normaal=date(post.begindatum.year,post.begindatum.month,1)
        if normaal<stop:
            overgeslagen.append(f'{post.omschrijving}: is vóór stoppen al ingegaan en blijft ongewijzigd.')
            continue
        if post.einddatum or post.waarde_periodes or post.frequentie==Frequentie.EENMALIG or post.bedrag_type!=BedragType.BRUTO:
            raise ValueError(f'{post.omschrijving}: gebruik voor deze raming een doorlopend bruto ouderdomspensioen zonder waardeperiodes.')
        if normaal.year>jaar_tot:
            raise ValueError(f'Verleng de berekeningsperiode tot minstens {normaal.year}, de oorspronkelijke pensioendatum van {post.omschrijving}.')
        deler={Frequentie.MAANDELIJKS:1,Frequentie.KWARTAAL:3,Frequentie.HALFJAARLIJKS:6,Frequentie.JAARLIJKS:12}[post.frequentie]
        bedrag=post.bedrag/Decimal(deler)
        actief=index not in keuze.reeds_opgebouwde_posten
        geschat=schat_regeling(bedrag,persoon.geboortedatum,stop,normaal,rente,post.groei_pct,startleeftijd,actief,opslag)
        gevoeligheid=[schat_regeling(bedrag,persoon.geboortedatum,stop,normaal,r,post.groei_pct,startleeftijd,actief,opslag) for r in sorted(rentes)]
        regel={'index':index,'naam':post.omschrijving,'normaal_vanaf':normaal,'direct_vanaf':stop,
               'import_bruto_maand':bedrag,'verdere_opbouw_aangenomen':actief,**geschat,
               'direct_laag':min(x['direct_bruto_maand'] for x in gevoeligheid),'direct_hoog':max(x['direct_bruto_maand'] for x in gevoeligheid),
               'premie_laag':min(x['premie_bruto_maand'] for x in gevoeligheid),'premie_hoog':max(x['premie_bruto_maand'] for x in gevoeligheid)}
        regels.append(regel)
        for variant,veld,ingang in zip(scenarios,['direct_bruto_maand','wachten_bruto_maand','doorbetalen_bruto_maand'],[stop,normaal,normaal]):
            component=variant.componenten[index]
            component.bedrag=geschat[veld]
            component.begindatum=ingang
            component.frequentie=Frequentie.MAANDELIJKS
        if normaal>stop and geschat['premie_bruto_maand']>0:
            scenarios[2].componenten.append(FinancieelComponent(
                omschrijving=f'Geschatte voortzettingspremie: {post.omschrijving}',categorie=CategorieComponent.UITGAVE,
                persoon=keuze.persoon,bedrag=geschat['premie_bruto_maand'],bedrag_type=BedragType.NETTO,
                begindatum=stop,einddatum=normaal-timedelta(days=1)))
    if not regels:
        raise ValueError('Geen nog in te gaan pensioenpost gevonden voor deze persoon. Controleer de pensioen- en stopdatums in je scenario.')
    return scenarios,{'persoon':keuze.persoon,'scenario':basis.naam,'laatste_werkdag':laatste,'vanaf_stoppen':stop,
        'rekenrente_pct':rente,'startleeftijd_opbouw':startleeftijd,'premie_kostenopslag_pct':opslag,
        'gevoeligheid_rentes_pct':sorted(rentes),'regelingen':regels,'overgeslagen':overgeslagen,
        'totaal_direct_bruto_maand':sum((r['direct_bruto_maand'] for r in regels),Decimal('0')),
        'totaal_wachten_bruto_maand':sum((r['wachten_bruto_maand'] for r in regels),Decimal('0')),
        'totaal_doorbetalen_bruto_maand':sum((r['doorbetalen_bruto_maand'] for r in regels),Decimal('0')),
        'premie_per_maand_bij_start':sum((r['premie_bruto_maand'] for r in regels),Decimal('0')),
        'bron_sterfte':'AG2024, cohortsterfte met 50/50 mix mannen/vrouwen, tot leeftijd 120',
        'aannames':[
            'Stopdatum, oorspronkelijke pensioenstart en bedragen komen uit het actieve scenario. Uitkeringen worden per kalendermaand verwerkt; direct betekent vanaf de maand na de laatste werkdag.',
            f'Bij ontbrekende opbouwhistorie nemen we lineaire opbouw vanaf {startleeftijd} jaar tot de oorspronkelijke pensioendatum aan. Dit is een carrièreproxy, geen vastgestelde pensioenaanspraak.',
            'Toekomstige pensioenposten worden voorlopig als te bereiken pensioen met verdere opbouw behandeld. Vink bij eerdere werkgevers/reeds opgebouwd pensioen de opbouwkorting uit onder Aannames.',
            'De vervroegingsfactor vergelijkt overlevingsgewogen contante waarden van maanduitkeringen met AG2024. De rekenrente is een aanname, geen actuele rentecurve van een fonds.',
            'De premie financiert actuarieel de geschatte ontbrekende opbouw, met een expliciete kostenopslag. Het is geen reglementaire fondspremie en vrijwillige voortzetting kan beperkt zijn.',
            'De gevoeligheidsmarge varieert alleen de rekenrente en is geen betrouwbaarheidsinterval. Salarisverloop, partnerpensioen, fondssterfte en Wtp-transitie kunnen de uitkomst veranderen.',
            'Er wordt geen belastingaftrek voor de voortzettingspremie toegepast. Netto bedragen volgen de bestaande belastingengine; AOW wordt niet vervroegd.',
            'Bestaande groei/indexatie uit je pensioenposten blijft gelden. Andere inkomsten, vermogen en de partner veranderen niet.',
        ]}
