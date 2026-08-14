import fs from 'node:fs'

const [path, mode] = process.argv.slice(2)
const pkg = JSON.parse(fs.readFileSync(path, 'utf8'))
for (const group of ['dependencies', 'devDependencies', 'optionalDependencies']) {
  if (!pkg[group]) continue
  for (const name of Object.keys(pkg[group])) {
    if (/(@esbuild\/(win32|darwin)|@rollup\/rollup-(win32|darwin)|fsevents)/.test(name)) delete pkg[group][name]
  }
}
pkg.devDependencies ??= {}
if (mode !== 'vue2') {
  pkg.devDependencies['@esbuild/linux-x64'] ??= '0.20.2'
  pkg.devDependencies['@rollup/rollup-linux-x64-gnu'] ??= '4.14.3'
} else if (pkg.scripts) {
  delete pkg.scripts.postinstall
}
fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n')

