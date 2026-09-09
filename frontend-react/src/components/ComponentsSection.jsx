import { useState } from "react";

export default function ComponentsSection({
  SectionHeader,
  NewPostPicker,
  PostCard,
  typeConfig,
  fieldMeta,
  inkomstenTypes,
  inkomenType,
  setInkomenType,
  addPost,
  inkomstenPosts,
  updatePost,
  removePost,
  removePosts,
  vermogenTypes,
  vermogenType,
  setVermogenType,
  vermogenPosts,
  payloadPreview,
  layoutVariant,
  setLayoutVariant,
}) {
  const [selectie, setSelectie] = useState([]);
  const [bevestigen, setBevestigen] = useState(false);
  const [melding, setMelding] = useState("");
  const allePosten = [...inkomstenPosts, ...vermogenPosts];
  const geselecteerd = allePosten.filter(post => selectie.includes(post.id));
  const kies = (ids) => { setSelectie(ids); setBevestigen(false); setMelding(""); };
  const verwijderSelectie = () => {
    removePosts(geselecteerd.map(post => post.id));
    setMelding(`${geselecteerd.length} posten verwijderd. Bereken je plan opnieuw voor actuele resultaten.`);
    setSelectie([]); setBevestigen(false);
  };
  const categories = [
    {
      id: "inkomsten",
      title: "Inkomsten & uitgaven",
      description: "Wat komt er binnen en wat gaat er uit?",
      options: inkomstenTypes,
      value: inkomenType,
      setValue: setInkomenType,
      posts: inkomstenPosts,
    },
    {
      id: "vermogen",
      title: "Vermogen",
      description: "Wat bezit je en welke schulden staan daar tegenover?",
      options: vermogenTypes,
      value: vermogenType,
      setValue: setVermogenType,
      posts: vermogenPosts,
    },
  ];

  const variantCopy = {
    color: {
      number: "01",
      title: "Kleur & herkenning",
      description: "Dezelfde vertrouwde indeling, met kleur als wegwijzer tussen geldstromen en vermogen.",
    },
    scale: {
      number: "02",
      title: "Zakelijk overzicht",
      description: "Een functionele werkweergave met heldere hiërarchie, vaste uitlijning en een rustig zakelijk kleurenpalet.",
    },
    masterpiece: {
      number: "03",
      title: "Financieel werkblad",
      description: "Een taakgerichte werkruimte: eerst kiezen, dan toevoegen, daarna controleren en verfijnen.",
    },
  };

  return (
    <div className={`components-page variant-${layoutVariant}`}>
      <header className="components-intro">
        <div>
          <p className="eyebrow">Je financiële situatie</p>
          <h1>Inkomen & vermogen</h1>
          <p>Vul in wat er binnenkomt, wat je uitgeeft en wat je hebt opgebouwd.</p>
        </div>
        <details className="view-settings">
          <summary>Weergave aanpassen</summary>
          <div className="layout-switcher" role="group" aria-label="Kies een weergave">
          {Object.entries(variantCopy).map(([key, copy]) => (
            <button
              key={key}
              type="button"
              className={layoutVariant === key ? "is-active" : ""}
              aria-pressed={layoutVariant === key}
              onClick={() => setLayoutVariant(key)}
            >
              <span>{copy.number}</span>
              {copy.title}
            </button>
          ))}
          </div>
        </details>
      </header>

      {removePosts ? <section className="bulk-post-actions" aria-label="Meerdere posten beheren">
        <div className="bulk-post-toolbar">
          <strong>{geselecteerd.length} posten geselecteerd</strong>
          <button type="button" className="ghost" disabled={!allePosten.length} onClick={() => kies(allePosten.map(post => post.id))}>Selecteer alle posten</button>
          <button type="button" className="ghost" disabled={!geselecteerd.length} onClick={() => kies([])}>Selectie wissen</button>
          <button type="button" disabled={!geselecteerd.length} onClick={() => setBevestigen(true)}>Verwijder selectie…</button>
        </div>
        {bevestigen && geselecteerd.length > 0 ? <div className="bulk-post-confirmation">
          <h2>Deze {geselecteerd.length} posten verwijderen?</h2>
          <ul>{geselecteerd.map(post => <li key={post.id}>{post.titel || typeConfig[post.type].label}{post.values?.persoon ? ` · ${post.values.persoon}` : ""}</li>)}</ul>
          <p>De posten worden uit het actieve scenario verwijderd.</p>
          <button type="button" onClick={verwijderSelectie}>Verwijder {geselecteerd.length} posten</button>{" "}
          <button type="button" className="ghost" onClick={() => setBevestigen(false)}>Annuleren</button>
        </div> : null}
        <p role="status">{melding}</p>
      </section> : null}

      {layoutVariant === "masterpiece" ? (
        <section className="component-command">
          <div>
            <span className="command-kicker">Snel toevoegen</span>
            <h2>Wat wil je vastleggen?</h2>
            <p>Kies een soort post. De nieuwe kaart verschijnt direct in het juiste overzicht.</p>
          </div>
          <div className="command-actions">
            {categories.map((category) => (
              <NewPostPicker
                key={category.id}
                title={category.title}
                options={category.options}
                value={category.value}
                onValueChange={category.setValue}
                onAdd={() => addPost(category.value)}
                labelMap={Object.fromEntries(category.options.map((option) => [option, typeConfig[option].label]))}
              />
            ))}
          </div>
        </section>
      ) : null}

      <div className="component-groups">
        {categories.map((category, index) => (
          <section className={`section component-group group-${category.id}`} key={category.id}>
            <div className="group-heading">
              <span className="group-index">0{index + 1}</span>
              <div>
                <SectionHeader title={category.title} description={category.description} />
                <span className="item-count">{category.posts.length} {category.posts.length === 1 ? "post" : "posten"}</span>
              </div>
            </div>

            {layoutVariant !== "masterpiece" ? (
              <NewPostPicker
                title="Nieuwe post"
                options={category.options}
                value={category.value}
                onValueChange={category.setValue}
                onAdd={() => addPost(category.value)}
                labelMap={Object.fromEntries(category.options.map((option) => [option, typeConfig[option].label]))}
              />
            ) : null}

            {category.posts.length > 0 ? (
              <div className="tiles">
                {category.posts.map((post) => (
                  <div key={post.id} className={`selectable-post ${selectie.includes(post.id) ? "is-selected" : ""}`}>
                    {removePosts ? <label className="post-selection"><input type="checkbox" checked={selectie.includes(post.id)} onChange={event => kies(event.target.checked ? [...selectie, post.id] : selectie.filter(id => id !== post.id))} />Selecteer {post.titel || typeConfig[post.type].label}{post.values?.persoon ? ` · ${post.values.persoon}` : ""}</label> : null}
                    <PostCard post={post} onChange={updatePost} onDelete={removePost} config={typeConfig[post.type]} fieldMeta={fieldMeta} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-component">
                <strong>Nog geen posten</strong>
                <span>Voeg hierboven de eerste post toe.</span>
              </div>
            )}
          </section>
        ))}
      </div>

      <details className="section payload-details">
        <summary>
          <span>Technische gegevens</span>
          <small>JSON voor API-koppeling</small>
          <span className="chevron" aria-hidden="true">⌄</span>
        </summary>
        <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
      </details>
    </div>
  );
}
