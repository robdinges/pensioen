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
  vermogenTypes,
  vermogenType,
  setVermogenType,
  vermogenPosts,
  payloadPreview,
}) {
  return (
    <>
      <section className="section">
        <SectionHeader title="Inkomsten / Uitgaven" description="Loon, uitkering, pensioen en eenmalige inkomsten/uitgaven als losse tegels." />
        <NewPostPicker title="Nieuwe post" options={inkomstenTypes} value={inkomenType} onValueChange={setInkomenType} onAdd={() => addPost(inkomenType)} labelMap={Object.fromEntries(inkomstenTypes.map((option) => [option, typeConfig[option].label]))} />
        <div className="tiles">{inkomstenPosts.map((post) => <PostCard key={post.id} post={post} onChange={updatePost} onDelete={removePost} config={typeConfig[post.type]} fieldMeta={fieldMeta} />)}</div>
      </section>

      <section className="section">
        <SectionHeader title="Vermogen" description="Sparen, beleggen, eigen woning, overige bezittingen en schulden (hypotheek)." />
        <NewPostPicker title="Nieuwe post" options={vermogenTypes} value={vermogenType} onValueChange={setVermogenType} onAdd={() => addPost(vermogenType)} labelMap={Object.fromEntries(vermogenTypes.map((option) => [option, typeConfig[option].label]))} />
        <div className="tiles">{vermogenPosts.map((post) => <PostCard key={post.id} post={post} onChange={updatePost} onDelete={removePost} config={typeConfig[post.type]} fieldMeta={fieldMeta} />)}</div>
      </section>

      <section className="section">
        <SectionHeader title="JSON Preview" description="Voor API-koppeling: actuele UI-invoer als JSON-structuur." />
        <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
      </section>
    </>
  );
}