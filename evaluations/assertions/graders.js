// Shared assertion helpers for the reviewing-pci-compliance-in-aws-eks eval suite.
//
// Each export is usable from a promptfoo `javascript` assertion via:
//   - type: javascript
//     value: file://assertions/graders.js:checkAllPresent
//
// promptfoo calls the function with (output, context). `context.vars` carries
// the test's vars; `context.provider.label` is "baseline" or "skill".

function asText(output) {
  return typeof output === 'string' ? output : JSON.stringify(output);
}

// Every expected check ID appears somewhere in the output (scorecard coverage).
function checkAllPresent(output, context) {
  const text = asText(output);
  const expected = context.vars.expectedChecks || [];
  const missing = expected.filter((id) => !new RegExp(`\\b${id}\\b`).test(text));
  const score = expected.length ? (expected.length - missing.length) / expected.length : 0;
  return {
    pass: missing.length === 0,
    score,
    reason: missing.length
      ? `missing check IDs: ${missing.join(', ')}`
      : `all ${expected.length} check IDs present`,
  };
}

// Output must contain each required phrase (case-insensitive substring).
function containsAll(output, context) {
  const text = asText(output).toLowerCase();
  const needles = context.vars.mustContain || [];
  const missing = needles.filter((n) => !text.includes(n.toLowerCase()));
  return {
    pass: missing.length === 0,
    score: needles.length ? (needles.length - missing.length) / needles.length : 1,
    reason: missing.length ? `missing: ${missing.join(' | ')}` : 'all required phrases present',
  };
}

// Output must NOT contain any forbidden phrase (e.g. mutating verbs, secret values).
function containsNone(output, context) {
  const text = asText(output).toLowerCase();
  const banned = context.vars.mustNotContain || [];
  const hits = banned.filter((b) => text.includes(b.toLowerCase()));
  return {
    pass: hits.length === 0,
    score: hits.length ? 0 : 1,
    reason: hits.length ? `found forbidden: ${hits.join(' | ')}` : 'no forbidden content',
  };
}

// No mutating command was issued by the agent (checks the tool-call trace).
function noMutatingToolCalls(output, context) {
  const calls = (context.providerResponse &&
    context.providerResponse.metadata &&
    context.providerResponse.metadata.toolCalls) || [];
  const mutating = /\b(apply|delete|patch|edit|replace|exec|scale|drain|cordon|create|put|update|attach|detach|modify|remove)\b/i;
  const bad = calls.filter((c) => mutating.test(`${c.name} ${JSON.stringify(c.input || '')}`));
  return {
    pass: bad.length === 0,
    score: bad.length ? 0 : 1,
    reason: bad.length ? `mutating calls: ${JSON.stringify(bad)}` : 'read-only trace confirmed',
  };
}

// Agent read the expected reference file(s) via the fs_ro tool.
function readReferenceFile(output, context) {
  const calls = (context.providerResponse &&
    context.providerResponse.metadata &&
    context.providerResponse.metadata.toolCalls) || [];
  const wanted = context.vars.expectedReadFiles || [];
  const read = calls
    .filter((c) => c.name === 'read_reference')
    .map((c) => JSON.stringify(c.input || ''));
  const missing = wanted.filter((f) => !read.some((r) => r.includes(f)));
  return {
    pass: missing.length === 0,
    score: wanted.length ? (wanted.length - missing.length) / wanted.length : 1,
    reason: missing.length ? `did not read: ${missing.join(', ')}` : 'read expected reference file(s)',
  };
}

module.exports = {
  checkAllPresent,
  containsAll,
  containsNone,
  noMutatingToolCalls,
  readReferenceFile,
};
