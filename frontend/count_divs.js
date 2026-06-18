const fs = require('fs');
const c = fs.readFileSync('./src/views/Dashboard.vue', 'utf8');
const opens = [], selfCloses = [], closes = [];
let lineNum = 0;
for (const line of c.split('\n')) {
  lineNum++;
  const trimmed = line.trim();
  // Self-closing: ends with />
  if (/<div[^>]*\/>/.test(trimmed)) { selfCloses.push(lineNum); continue; }
  // Non-self-closing open: <div ... > (not self-closing)
  if (/<div/.test(trimmed)) { opens.push(lineNum); continue; }
  // Closing tag
  if (/<\/div>/.test(trimmed)) closes.push(lineNum);
}
console.log('Non-self-close opens:', opens.length);
console.log('Self-closes:', selfCloses.length);
console.log('Closes:', closes.length);
console.log('Net:', opens.length + selfCloses.length - closes.length);
console.log('Opens:', opens);
console.log('Self:', selfCloses);
console.log('Closes:', closes);