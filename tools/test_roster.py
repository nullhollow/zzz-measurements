"""Regression checks for missing values and shareable table state."""
import subprocess
from pathlib import Path
source=Path(__file__).with_name('roster.js').read_text().split('function renderColumnPicker')[0]
checks=r'''
const assert=require('node:assert/strict');
for(const dir of [1,-1]){
 const a=[4,null,2,undefined,3].sort((a,b)=>compareTableValues(a,b,dir,true,'en'));
 assert.deepEqual(a.slice(0,3),dir===1?[2,3,4]:[4,3,2]);
 assert.equal(compareTableValues(null,3,dir,true,'en'),1);
 assert.equal(compareTableValues(3,null,dir,true,'en'),-1);
 assert.equal(compareTableValues(null,null,dir,true,'en'),0);
}
assert.deepEqual(parseTableSort('thigh:-1'),{k:'thigh',dir:-1});
for(const x of ['oops:1','height:0',null,'__proto__:1'])assert.deepEqual(parseTableSort(x),{k:'uk',dir:-1});
assert.deepEqual(parseTableColumns('uk,uk,name,height,invalid'),['uk','height']);
assert.equal(parseTableColumns('invalid'),null);
'''
subprocess.run(['node','-e',source+checks],check=True)
print('Roster sorting and URL validation passed')
