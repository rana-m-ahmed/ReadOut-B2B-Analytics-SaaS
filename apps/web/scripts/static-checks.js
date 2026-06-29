/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require('fs');
const path = require('path');

console.log('Running static checks...');
let failed = false;

function walkDir(dir, callback) {
  if (!fs.existsSync(dir)) return;
  fs.readdirSync(dir).forEach(f => {
    const dirPath = path.join(dir, f);
    const isDirectory = fs.statSync(dirPath).isDirectory();
    if (isDirectory) {
      walkDir(dirPath, callback);
    } else {
      callback(path.join(dir, f));
    }
  });
}

function checkFiles(dirs, regex, errorMessage, ignorePatterns = []) {
  dirs.forEach(dir => {
    walkDir(dir, (filePath) => {
      // Only check ts, tsx, css files
      if (!/\.(ts|tsx|css)$/.test(filePath)) return;
      
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, i) => {
        if (regex.test(line)) {
          if (!ignorePatterns.some(p => line.includes(p) || filePath.includes(p))) {
            console.error(`\x1b[31m[FAIL]\x1b[0m ${errorMessage}`);
            console.error(`  ${filePath}:${i + 1}: ${line.trim()}`);
            failed = true;
          }
        }
      });
    });
  });
}

const dirsToCheck = ['components', 'app', 'lib', 'styles'].map(d => path.join(__dirname, '..', d));

// 1. No stray hex colors outside tokens
checkFiles(
  dirsToCheck,
  /#[0-9a-fA-F]{3,6}\b/,
  'Found inline hex colors instead of CSS variables:',
  ['tokens.css', 'eslint-disable'] // allow in tokens
);

// 2. No inline spring constants outside lib/motion.ts
checkFiles(
  dirsToCheck,
  /type:\s*["']spring["']/,
  'Found inline spring configurations. Use constants from lib/motion.ts:',
  ['motion.ts']
);

// 3. No direct fetch outside lib/api/client.ts
checkFiles(
  dirsToCheck,
  /[^a-zA-Z]fetch\(/,
  'Found direct fetch calls outside API client:',
  ['apiFetch', 'client.ts']
);

// 4. No TODO/Lorem/unlabeled placeholders
checkFiles(
  dirsToCheck,
  /todo|lorem|placeholder/i,
  'Found placeholder text or TODOs:',
  ['placeholder=', 'placeholder:', 'placeholder'] // ignore HTML/CSS placeholder attributes and variable names
);

if (failed) {
  console.error('\n\x1b[31mStatic checks failed.\x1b[0m');
  process.exit(1);
} else {
  console.log('\x1b[32mAll static checks passed!\x1b[0m');
}
