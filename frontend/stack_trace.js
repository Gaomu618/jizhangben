const fs = require('fs');
const content = fs.readFileSync('./src/views/Dashboard.vue', 'utf8');
const lines = content.split('\n');
const depth = 0;
const stack = [];

for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('</template>')) break;
    if (lines[i].includes('<!--')) continue;

    const o = (lines[i].match(/<div(?!\/)/g) || []).length;
    const c = (lines[i].match(/<\/div>/g) || []).length;

    for (let j = 0; j < o; j++) stack.push(i+1);
    for (let j = 0; j < c; j++) {
        if (stack.length === 0) {
            console.log("UNDERFLOW at line " + (i+1) + ": " + lines[i].trim());
        } else {
            const openedAt = stack.pop();
            console.log("L" + (i+1) + " closes div from L" + openedAt + "  " + lines[i].trim().substring(0, 60));
        }
    }
}

console.log("Stack size at end: " + stack.length);
if (stack.length > 0) console.log("Unclosed divs opened at: " + stack.join(', '));