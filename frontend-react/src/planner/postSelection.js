export function removeSelectedPosts(posts, ids) {
  const selected = new Set(ids);
  return posts.filter(post => !selected.has(post.id));
}
