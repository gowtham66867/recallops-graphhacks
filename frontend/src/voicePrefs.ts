export const languages={'en-IN':'English','hi-IN':'हिन्दी','kn-IN':'ಕನ್ನಡ','hi-Latn':'Hinglish'} as const;
export type Language=keyof typeof languages;
export type VoicePrefs={enabled:boolean;language:Language;provider:'device'|'gemini';pause:number;autoStop:boolean};
export const defaults:VoicePrefs={enabled:false,language:'en-IN',provider:'device',pause:2000,autoStop:true};
export function loadPrefs(storage:Pick<Storage,'getItem'>):VoicePrefs{try{const p=JSON.parse(storage.getItem('recallops-voice-v1')||'{}');return {enabled:p.enabled===true,language:Object.hasOwn(languages,p.language)?p.language:'en-IN',provider:p.provider==='gemini'?'gemini':'device',pause:[1200,2000,3500].includes(p.pause)?p.pause:2000,autoStop:p.autoStop!==false}}catch{return {...defaults}}}
export function savePrefs(storage:Pick<Storage,'setItem'>,p:VoicePrefs){try{storage.setItem('recallops-voice-v1',JSON.stringify(p));return true}catch{return false}}

export function browserPrefs():VoicePrefs{try{return loadPrefs(window.localStorage)}catch{return {...defaults}}}
export function persistBrowserPrefs(p:VoicePrefs){try{return savePrefs(window.localStorage,p)}catch{return false}}
