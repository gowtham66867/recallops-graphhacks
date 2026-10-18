import test from 'node:test';
import assert from 'node:assert/strict';
import {loadPrefs,savePrefs,defaults} from '../src/voicePrefs.ts';
import {createVadGate} from '../src/voiceActivity.ts';

test('spoken preference survives a fresh read after reload',()=>{
 let value:string|null=null;const storage={getItem:()=>value,setItem:(_key:string,v:string)=>{value=v}};
 assert.equal(savePrefs(storage,{...defaults,enabled:true,language:'kn-IN',pause:3500}),true);
 const reloaded=loadPrefs(storage);assert.equal(reloaded.enabled,true);assert.equal(reloaded.language,'kn-IN');assert.equal(reloaded.pause,3500);
 assert.equal(value?.includes('consent'),false);
});
test('missing and malformed storage defaults to voice off',()=>{
 assert.equal(loadPrefs({getItem:()=>null}).enabled,false);
 assert.deepEqual(loadPrefs({getItem:()=>'{broken'}),defaults);
});
test('unknown language, provider and pause values cannot enter restored controls',()=>{
 const p=loadPrefs({getItem:()=>JSON.stringify({language:'__proto__',provider:'external-url',pause:10,enabled:'true'})});
 assert.deepEqual(p,defaults);
});
test('unavailable storage has explicit safe fallback',()=>{
 assert.deepEqual(loadPrefs({getItem:()=>{throw Error('blocked')}}),defaults);
 assert.equal(savePrefs({setItem:()=>{throw Error('blocked')}},defaults),false);
});
test('an unsupported future preference does not restore consent',()=>{
 const p=loadPrefs({getItem:()=>JSON.stringify({enabled:true,consent:true,language:'hi-Latn'})});
 assert.equal(p.enabled,true);assert.equal('consent' in p,false);
});
test('silence and a short click are discarded locally',()=>{
 const gate=createVadGate(0,2000);assert.equal(gate(.001,0),'recording');gate(.1,100);gate(.001,150);assert.equal(gate(.001,10000),'no_speech');
});
test('sustained speech followed by the selected pause stops',()=>{
 const gate=createVadGate(0,2000);gate(.1,100);gate(.1,300);assert.equal(gate(.001,2000),'recording');assert.equal(gate(.001,2300),'pause');
});
test('a thinking pause can resume and extended-pause mode waits longer',()=>{
 const gate=createVadGate(0,3500);gate(.1,100);gate(.1,400);assert.equal(gate(.001,2500),'recording');gate(.1,2800);assert.equal(gate(.001,6000),'recording');assert.equal(gate(.001,6300),'pause');
});
