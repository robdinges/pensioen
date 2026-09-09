import assert from 'node:assert/strict';
import { test } from 'node:test';
import { removeSelectedPosts } from '../src/planner/postSelection.js';
test('bulk deletion targets IDs, preserves other posts and never mutates the source', () => {
  const posts = Object.freeze([
    Object.freeze({id: 'a', titel: 'Pensioen', values: {persoon: 'P1'}}),
    Object.freeze({id: 'b', titel: 'Pensioen', values: {persoon: 'P2'}}),
    Object.freeze({id: 'c', titel: 'Sparen'}),
  ]);
  const result = removeSelectedPosts(posts, ['a', 'c', 'a', 'missing']);
  assert.deepEqual(result, [posts[1]]);
  assert.equal(result[0], posts[1]);
  assert.equal(posts.length, 3);
  assert.deepEqual(removeSelectedPosts(posts, []), posts);
  assert.deepEqual(removeSelectedPosts(posts, ['a', 'b', 'c']), []);
});
