// SPDX-License-Identifier: AGPL-3.0-only
import fs from 'node:fs';
import {LANGUAGES,catalogs} from '../web/i18n.mjs';
let errors=0;for(const {code} of LANGUAGES){const missing=Object.keys(catalogs.en).filter(k=>typeof catalogs[code][k]!=='string'||!catalogs[code][k]);if(missing.length){console.error(code,missing);errors+=missing.length;}console.log(code,Object.keys(catalogs[code]).length+' entries');}
if(errors)process.exitCode=1;else console.log('Catalog coverage complete. Linguistic and financial review remains a separate human check.');
