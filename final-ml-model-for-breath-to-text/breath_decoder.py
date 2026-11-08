"""Five-breath codes and silence-based word/send controls."""
from itertools import product

ALL_CODES=[''.join(digits) for digits in product('12',repeat=5)]
CODES=dict(zip(ALL_CODES[:26],'ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
DELETE_CODE=ALL_CODES[26]
MAX_CODE_LENGTH=5

class Decoder:
    def __init__(self,letter_gap=.8,word_gap=2.0,send_gap=4.0):
        if not 0<letter_gap<word_gap<send_gap:raise ValueError('Timing must satisfy 0 < letter gap < word gap < send gap')
        self.letter_gap,self.word_gap,self.send_gap=letter_gap,word_gap,send_gap
        self.reset()
    def reset(self):
        self.current='SILENCE';self.silence=0.;self.code='';self.cooldown=False
        self.word_pending=False;self.send_armed=False
    def advance(self,state,dt=.05):
        if state not in ('SILENCE','INHALE','EXHALE') or dt<=0:raise ValueError('Expected a positive-duration classified breath window')
        events=[];epsilon=1e-9
        if self.cooldown:
            self.current=state
            if state=='SILENCE':
                self.silence+=dt
                if self.silence+epsilon>=self.letter_gap:self.cooldown=False
            else:self.silence=0.
        else:
            if state!=self.current:
                if self.current in ('INHALE','EXHALE'):
                    self.code+='1' if self.current=='INHALE' else '2'
                    events.append(('digit',self.code))
                    if len(self.code)==MAX_CODE_LENGTH:
                        code,self.code=self.code,''
                        if code==DELETE_CODE:events.append(('delete',None));self.word_pending=False;self.send_armed=True
                        elif code in CODES:events.append(('letter',CODES[code]));self.word_pending=True;self.send_armed=True
                        else:events.append(('invalid',code));self.word_pending=False;self.send_armed=False
                        self.cooldown=True
                if state!='SILENCE':
                    self.silence=0.
                    if not self.cooldown:self.word_pending=False;self.send_armed=False
                self.current=state
            if state=='SILENCE':self.silence+=dt
        if state=='SILENCE':
            if self.code and self.silence+epsilon>=self.word_gap:
                events.append(('incomplete',self.code));self.code='';self.word_pending=False;self.send_armed=False
            if self.word_pending and self.silence+epsilon>=self.word_gap:
                events.append(('space',None));self.word_pending=False
            if self.send_armed and self.silence+epsilon>=self.send_gap:
                events.append(('send',None));self.send_armed=False
        return events
