import fs from 'fs'
const ts = new Date().toISOString()
const f = `logs/${ts.slice(0,10)}.md`
fs.mkdirSync('logs',{recursive:true})
const entry = `- ${ts} • codex • ${process.argv.slice(2).join(' ')}`
fs.appendFileSync(f, entry+'\n')
console.log(entry)
