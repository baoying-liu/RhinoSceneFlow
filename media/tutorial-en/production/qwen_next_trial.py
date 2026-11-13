"""Reference-conditioned Next voice trial. Reads the private Windows vault only."""
import base64
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit
from qwen_credentials import load_credentials

TEXT = ('Welcome to SceneFlow. In this fifteen minute tutorial, we will turn a simple Rhino model '
        'into a finished architectural image. First, we will create a material and apply it at its real world size. '
        'Next, we will place plants and adjust their spacing. Then we will export a layered image, refine it with '
        'A I, and compare the result with the original. The model stays editable throughout the process.')


def main():
    credentials = load_credentials()
    folder = Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/production/voice-private'
    reference = folder/'baoying-reference-24k-mono.wav'
    if (folder/'SceneFlow-Baoying-Next-Trial.wav').exists():
        print(json.dumps({'completed':True,'reused_existing':True,'new_api_calls':0}))
        return
    text_prompt = ('A single speaker records a clean English software tutorial. '
        'Match the vocal identity of reference @voice1. Natural, calm, clear narration at a moderate pace. '
        'No music, sound effects, other speakers, or extra words. @voice1 says: "'+TEXT+'"')
    payload = {'model':'qwen-audio-3.1-tts-next','input':{'text_prompt':text_prompt,
        'references':[{'audio_data':'data:audio/wav;base64,'+base64.b64encode(reference.read_bytes()).decode()}],
        'format':'wav'}}
    request = urllib.request.Request(credentials['base_url']+'/api/v1/services/audio/tts/SpeechSynthesizer',
        data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+credentials['api_key'],
        'Content-Type':'application/json'})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request,timeout=180) as response:result=json.load(response)
    except urllib.error.HTTPError as error:
        try:code=json.loads(error.read()).get('code','HTTP_ERROR')
        except Exception:code='HTTP_ERROR'
        print(json.dumps({'completed':False,'model':payload['model'],'http':error.code,'code':str(code)[:100]}))
        return
    # Keep URL-bearing response private; never print credential, base64 or signed URL.
    (folder/'next-trial-response.private.json').write_text(json.dumps(result),encoding='utf8')
    audio=result.get('output',{}).get('audio',{})
    if audio.get('data'):content=base64.b64decode(audio['data'],validate=True)
    elif audio.get('url'):
        parsed=urlsplit(audio['url'])
        if parsed.scheme=='http' and parsed.hostname=='dashscope-result-sgp.oss-ap-southeast-1.aliyuncs.com':
            parsed=parsed._replace(scheme='https')
        if parsed.scheme!='https':raise RuntimeError('Audio download requires HTTPS')
        with urllib.request.urlopen(urlunsplit(parsed),timeout=55) as response:content=response.read()
    else:
        print(json.dumps({'completed':False,'model':payload['model'],'output_fields':list(result.get('output',{}))}))
        return
    output=folder/'SceneFlow-Baoying-Next-Trial.wav'
    output.write_bytes(content)
    receipt={'completed':True,'model':payload['model'],'reference_conditioned':True,
        'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'text':TEXT,
        'request_seconds':time.perf_counter()-start,'bytes':len(content),'usage':result.get('usage'),
        'finish_reason':result.get('output',{}).get('finish_reason')}
    (folder/'next-trial-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'completed':False,'error':type(error).__name__}))
        raise SystemExit(1)
