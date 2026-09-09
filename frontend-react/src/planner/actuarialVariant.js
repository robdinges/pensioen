import {TYPE_CONFIG, createPost} from './plannerCore.js';

// Restore only this person's pension inputs and remove only their generated premiums.
export function prepareActuarialSnapshot(snapshot, persoon) {
  const next = structuredClone(snapshot);
  const applied = next.opbouwDraft?.toegepast?.find(x => x.persoon === persoon);
  if (!applied) return next;
  if (!applied.basisPosten) throw new Error('Deze oudere keuze heeft nog geen oorspronkelijke pensioeninvoer. Open het oorspronkelijke scenario om opnieuw te kiezen.');
  const premiums = new Set(applied.premieIds || []);
  next.posts = next.posts.filter(p => !premiums.has(p.id));
  for (const original of applied.basisPosten) {
    const index = next.posts.findIndex(p => p.id === original.id);
    if (index < 0) throw new Error('Een oorspronkelijk pensioen is verwijderd. Herstel deze post voordat je de keuze wijzigt.');
    const last = applied.toegepastePosten?.find(p => p.id === original.id);
    if (last && JSON.stringify(next.posts[index].values) !== JSON.stringify(last.values))
      throw new Error('Een toegepast pensioenbedrag of datum is handmatig gewijzigd. Herstel die invoer voordat je opnieuw actuarieel kiest.');
    next.posts[index] = structuredClone(original);
  }
  return next;
}

// Apply engine amounts and dates; preserve all unrelated financial inputs.
export function applyActuarialVariant(snapshot, variant, raming, resultaat) {
  if (!raming.volledig) throw new Error('Een onvolledige raming kan niet als plan worden toegepast.');
  const next = prepareActuarialSnapshot(snapshot, raming.persoon);
  const basisPosten = [];
  const premieIds = [];
  const componentPosts = next.posts.filter(p => TYPE_CONFIG[p.type].section === 'inkomsten'
    && !['eenmalige_inkomsten', 'eenmalige_uitgaven'].includes(p.type));
  for (const row of raming.regelingen) {
    const post = componentPosts[row.index], component = variant.componenten[row.index];
    if (!post || post.type !== 'pensioen' || post.titel !== component.omschrijving)
      throw new Error('De pensioenposten zijn gewijzigd. Bereken de varianten opnieuw.');
    basisPosten.push(structuredClone(post));
    Object.assign(post.values, {
      bedrag: component.bedrag, startdatum: component.begindatum || '',
      einddatum: component.einddatum || '', frequentie: component.frequentie,
      bedrag_type: component.bedrag_type, inflatie_pct: component.groei_pct,
    });
  }
  for (const component of variant.componenten.slice(componentPosts.length)) {
    if (component.categorie !== 'uitgave') throw new Error('Onbekende toevoeging aan pensioenvariant.');
    const post = createPost('uitgave');
    post.titel = component.omschrijving;
    Object.assign(post.values, {persoon: component.persoon, bedrag: component.bedrag,
      bedrag_type: component.bedrag_type, frequentie: component.frequentie,
      startdatum: component.begindatum || '', einddatum: component.einddatum || '',
      inflatie_pct: component.groei_pct});
    next.posts.push(post);
    premieIds.push(post.id);
  }
  next.opbouwDraft = {...next.opbouwDraft, toegepast: [
    ...(next.opbouwDraft?.toegepast || []).filter(x => x.persoon !== raming.persoon),
    {persoon: raming.persoon, variant: variant.naam, aannames: raming.aannames, basisPosten, premieIds,
      toegepastePosten: next.posts.filter(p => basisPosten.some(b => b.id === p.id)).map(p => structuredClone(p))},
  ]};
  next.resultaat = resultaat;
  next.calculationStatus = 'fresh';
  next.inputSignatureAtCalculation = '';
  return next;
}
