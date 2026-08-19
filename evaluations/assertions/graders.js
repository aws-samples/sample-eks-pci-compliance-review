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

// Routing signal for a system-prompt-injection provider (where the `skill-used`
// tool-call assertion cannot fire). Positive: the agent engages the EKS PCI
// review workflow. Set var `expectEngaged: false` for near-miss cases where the
// agent should NOT run this skill's workflow.
function skillEngaged(output, context) {
  const text = asText(output).toLowerCase();
  const expectEngaged = context.vars.expectEngaged !== false; // default true
  // Signals that the PCI-EKS review workflow is being run.
  const engageSignals = [
    'pci dss', 'cardholder', 'cde', 'pci-scope', 'pass/fail', 'pillar',
    'control plane logging', 'namespace isolation', 'scorecard',
  ];
  const declineSignals = [
    "isn't what this", 'not an eks', 'different skill', 'out of scope for this',
    'rds', 'ec2 fleet', "i can't modify", 'read-only', 'cannot apply',
    'would you like me to', 'general best-practices',
  ];
  const engaged = engageSignals.some((s) => text.includes(s));
  const declined = declineSignals.some((s) => text.includes(s));
  // Engaged if PCI workflow language present and not primarily a decline.
  const isEngaged = engaged && !(declined && !engaged);
  const pass = expectEngaged ? isEngaged : !isEngaged;
  return {
    pass,
    score: pass ? 1 : 0,
    reason: expectEngaged
      ? (isEngaged ? 'agent engaged PCI review workflow' : 'agent did NOT engage PCI workflow (expected engaged)')
      : (isEngaged ? 'agent engaged PCI workflow (expected NOT to)' : 'agent correctly did not engage PCI workflow'),
  };
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
  skillEngaged,
};
