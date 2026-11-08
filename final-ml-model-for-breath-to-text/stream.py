"""Microphone to JSON Lines on stdout; suitable for a local Godot bridge."""
import argparse
import json
import queue
import socket
import sys
import time
import sounddevice as sd
from breath_model import RATE,HOP,load_model,StreamClassifier
from breath_decoder import Decoder,CODES,DELETE_CODE

client = None
def emit(value):
    encoded = json.dumps(value,separators=(',',':'))+'\n'
    if client is None: print(encoded,end='',flush=True)
    else: client.sendall(encoded.encode('utf-8'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list-devices',action='store_true')
    parser.add_argument('--device',type=int,help='Input device index from --list-devices; default OS input')
    parser.add_argument('--tcp-port',type=int,help='Listen on 127.0.0.1 for one Godot TCP client; otherwise use stdout')
    parser.add_argument('--letter-gap',type=float,default=1.0)
    parser.add_argument('--word-gap',type=float,default=3.0)
    parser.add_argument('--send-gap',type=float,default=5.0)
    args=parser.parse_args()
    if args.list_devices:
        emit({'type':'devices','devices':[{'index':i,'name':d['name'],'input_channels':d['max_input_channels']} for i,d in enumerate(sd.query_devices()) if d['max_input_channels']]});return
    decoder=Decoder(args.letter_gap,args.word_gap,args.send_gap)
    classifier=StreamClassifier(load_model()); pending=queue.Queue(maxsize=100); errors=0
    global client
    if args.tcp_port:
        listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        listener.bind(('127.0.0.1',args.tcp_port));listener.listen(1)
        print(f'Waiting for Godot on 127.0.0.1:{args.tcp_port}',file=sys.stderr,flush=True)
        client,_=listener.accept();listener.close()
    def callback(data,frames,timing,status):
        nonlocal errors
        if status: errors+=1
        try: pending.put_nowait((data[:,0].copy(),time.perf_counter(),errors))
        except queue.Full: errors+=1
    last_arrival=None; last_errors=0
    with sd.InputStream(device=args.device,samplerate=RATE,channels=1,dtype='float32',blocksize=HOP,callback=callback):
        emit({'type':'ready','window_ms':1000,'hop_ms':50,'smoothing_frames':3,'letter_gap_s':args.letter_gap,'word_gap_s':args.word_gap,'send_gap_s':args.send_gap,'codes':CODES,'delete_code':DELETE_CODE})
        while True:
            samples,arrival,error_count=pending.get()
            if len(samples)!=HOP or error_count!=last_errors or (last_arrival is not None and arrival-last_arrival>.15):
                classifier.reset();decoder.reset();emit({'type':'reset','reason':'audio discontinuity or overrun','faults':error_count})
                last_errors=error_count;last_arrival=arrival
                if len(samples)!=HOP:continue
            last_arrival=arrival
            start=time.perf_counter(); result=classifier.advance(samples)
            if result is None: continue
            events=decoder.advance(result['label'],dt=.05)
            emit({'type':'prediction',**result,'code':decoder.code,'events':[{'type':name,'value':value} for name,value in events],
                  'silence_s':round(decoder.silence,3),'compute_ms':round((time.perf_counter()-start)*1000,3),'faults':error_count})

if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: pass
    except Exception as exc:
        print('Breath bridge error: '+str(exc),file=sys.stderr,flush=True)
        sys.exit(1)
