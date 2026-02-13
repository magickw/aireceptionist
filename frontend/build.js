const fs = require('fs');
const { execSync } = require('child_process');

console.log('Cleaning .next directory...');
try {
  if (fs.existsSync('.next')) {
    fs.rmSync('.next', { recursive: true, force: true });
    console.log('.next directory removed');
  }
} catch (error) {
  console.error('Error removing .next:', error.message);
}

console.log('Running next build...');
execSync('npm run build', { stdio: 'inherit' });