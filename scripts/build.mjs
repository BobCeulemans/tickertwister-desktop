import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {build}=require('esbuild');
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bundle=process.argv[2]?path.resolve(process.argv[2]):path.join(root,'dist/Tickertwister Desktop.app');
const target=path.join(bundle,'Contents/Resources/Web');
fs.mkdirSync(target,{recursive:true});
await build({plugins:[{name:'report-styles',setup(build){build.onResolve({filter:/^report-styles$/},()=>({path:'report-styles',namespace:'report'}));build.onLoad({filter:/.*/,namespace:'report'},()=>({contents:'export default '+JSON.stringify(fs.readFileSync(path.join(root,'web/style.css'),'utf8')),loader:'js'}));}}],entryPoints:[path.join(root,'web/entry.jsx')],bundle:true,external:['./buffett-munger.png'],jsx:'automatic',format:'iife',platform:'browser',target:'safari16',nodePaths:[path.join(root,'node_modules')],outfile:path.join(target,'app.js'),minify:true,define:{'process.env.NODE_ENV':'"production"'},legalComments:'eof'});
for(const file of ['index.html','buffett-munger.png','app-icon.png'])fs.copyFileSync(path.join(root,'web',file),path.join(target,file));

fs.cpSync(path.join(root,'web/locales'),path.join(bundle,'Contents/Resources/Locales'),{recursive:true});
