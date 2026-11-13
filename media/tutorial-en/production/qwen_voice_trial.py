"""Explicit short voice-clone trial. Credentials/recording stay out of logs and Git."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from qwen_credentials import load_credentials

TEXT = 'Welcome to SceneFlow. Today we will create materials, place plants, and export a layered image from Rhino.'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--model', choices=['qwen-audio-3.1-tts-plus','qwen-audio-3.1-tts-flash'], default='qwen-audio-3.1-tts-plus')
    args = parser.parse_args()
    credential = load_credentials()
    folder = Path(os.environ['LOCALAPPDATA']) / 'RhinoSceneFlow/production/voice-private'
    folder.mkdir(parents=True, exist_ok=True)
    model = args.model
    def call(path, payload):
        req = urllib.request.Request(credential['base_url'] + '/api/v1/' + path,
            data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer '+credential['api_key'],
            'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=55) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            try: code = json.loads(error.read()).get('code', 'HTTP_ERROR')
            except Exception: code = 'HTTP_ERROR'
            # Never echo server messages (may repeat submitted data), headers or URLs.
            raise RuntimeError(f'Qwen HTTP {error.code}; code={str(code)[:100]}') from None
        return result
    service = 'services/audio/tts/customization'
    if args.probe:
        result = call(service, {'model':'voice-enrollment','input':{'action':'list_voice','prefix':'sftrial','page_index':0,'page_size':10}})
        print(json.dumps({'authenticated':True,'region':credential['region'],'probe':'voice list','has_output':'output' in result}))
        return
    reference = folder/'baoying-reference-24k-mono.wav'
    receipt_path = folder/('trial-voice-'+model+'.json')
    fingerprint = hashlib.sha256(reference.read_bytes()).hexdigest()
    voice = None
    if receipt_path.exists():
        saved = json.loads(receipt_path.read_text())
        if saved['model']==model and saved['region']==credential['region'] and saved['reference_sha256']==fingerprint:
            voice=saved['voice_id']
    if not voice:
        result=call(service, {'model':'voice-enrollment','input':{'action':'create_voice','target_model':model,
            'prefix':'sftrial','audio':'data:audio/wav;base64,'+base64.b64encode(reference.read_bytes()).decode()}})
        voice=result['output']['voice_id']
        receipt_path.write_text(json.dumps({'voice_id':voice,'model':model,'region':credential['region'],
            'reference_sha256':fingerprint},indent=2))
        print('Voice created; receipt saved privately.',flush=True)
    for _ in range(20):
        result=call(service, {'model':'voice-enrollment','input':{'action':'query_voice','voice_id':voice}})
        status=result['output']['status']
        if status=='OK':break
        if status!='DEPLOYING':raise RuntimeError('Voice was not accepted: '+str(status)[:50])
        time.sleep(2)
    else:raise RuntimeError('Voice not ready; reuse saved receipt on next run')
    print('Voice ready. Generating short English trial.',flush=True)
    result=call('services/audio/tts/SpeechSynthesizer',{'model':model,'input':{
        'text':TEXT,'voice':voice,'format':'wav','sample_rate':24000}})
    audio_result=result['output']['audio']
    if audio_result.get('data'):
        audio=base64.b64decode(audio_result['data'],validate=True)
    else:
        audio_url=audio_result.get('url','')
        if not audio_url.startswith('https://'):raise RuntimeError('Expected audio data or HTTPS result')
        with urllib.request.urlopen(audio_url,timeout=55) as response:audio=response.read()
    output=folder/('SceneFlow-Baoying-'+model+'-Trial.wav')
    output.write_bytes(audio)
    (folder/'trial-text.txt').write_text(TEXT,encoding='utf8')
    print(json.dumps({'completed':True,'audio_file':str(output),'bytes':len(audio),'characters':len(TEXT)}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        # Exceptions generated above are safe; other exceptions reveal only their type.
        message=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print(json.dumps({'completed':False,'error':message}))
        raise SystemExit(1)
