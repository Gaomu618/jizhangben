// Simple zero-dependency test runner
// Usage:
//   const { describe, it, assertEqual, assertTruthy, assertMatch, assertDeepEqual } = require('./runner')

let pass = 0, fail = 0
const failures = []

function describe(name, fn) {
  console.log(`\n\x1b[1m\x1b[36m=== ${name} ===\x1b[0m`)
  fn()
}

function it(name, fn) {
  try {
    fn()
    pass++
    console.log(`  \x1b[32m✓\x1b[0m ${name}`)
  } catch (e) {
    fail++
    failures.push({ name, error: e })
    console.log(`  \x1b[31m✗\x1b[0m ${name}`)
    console.log(`    \x1b[31m${e.message}\x1b[0m`)
  }
}

function assertEqual(actual, expected, msg) {
  if (actual !== expected) {
    throw new Error(`${msg || ''}  expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

function assertDeepEqual(actual, expected, msg) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${msg || ''}  expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

function assertTruthy(val, msg) {
  if (!val) throw new Error(`${msg || ''}  expected truthy, got ${JSON.stringify(val)}`)
}

function assertFalsy(val, msg) {
  if (val) throw new Error(`${msg || ''}  expected falsy, got ${JSON.stringify(val)}`)
}

function assertMatch(actual, pattern, msg) {
  if (typeof pattern === 'string') pattern = new RegExp(pattern)
  if (!pattern.test(actual)) {
    throw new Error(`${msg || ''}  expected match ${pattern}, got ${JSON.stringify(actual)}`)
  }
}

function assertThrows(fn, msg) {
  let threw = false
  try { fn() } catch (e) { threw = true }
  if (!threw) throw new Error(`${msg || ''}  expected function to throw`)
}

function summary() {
  console.log(`\n\x1b[1m${'='.repeat(50)}\x1b[0m`)
  console.log(`\x1b[1mTotal: ${pass + fail}  \x1b[32mPassed: ${pass}\x1b[0m  \x1b[31mFailed: ${fail}\x1b[0m`)
  if (fail > 0) {
    console.log('\n\x1b[31mFailures:\x1b[0m')
    failures.forEach(f => console.log(`  - ${f.name}: ${f.error.message}`))
  }
  return fail
}

module.exports = {
  describe, it,
  assertEqual, assertDeepEqual,
  assertTruthy, assertFalsy, assertMatch,
  assertThrows,
  summary
}