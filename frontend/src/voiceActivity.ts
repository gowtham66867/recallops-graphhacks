// A bounded energy gate; it does not infer semantic completion or speech content.
export function createVadGate(started:number,pauseMs:number){
 let hasVoice=false,voiceStart:number|null=null,lastVoice=started;
 return (rms:number,now:number):'recording'|'no_speech'|'pause'=>{
  if(rms>.025){if(voiceStart===null)voiceStart=now;if(now-voiceStart>=200)hasVoice=true;lastVoice=now}else voiceStart=null;
  if(!hasVoice&&now-started>=10000)return 'no_speech';
  if(hasVoice&&now-lastVoice>=pauseMs)return 'pause';
  return 'recording';
 }
}
