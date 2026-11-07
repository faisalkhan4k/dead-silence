"""Frame-based breath-to-letter protocol; thresholds are provisional."""
CODES = dict(zip(['1','2','11','12','21','22','111','112','121','122','211','212','221','222','1111','1112','1121','1122','1211','1212','1221','1222','2111','2112','2121','2122'],
                 'ET AOINSHRDLUCMFWGYPBVKJXQZ'.replace(' ','')))

class Decoder:
    def __init__(self, letter_gap=.8, word_gap=2.0, long_breath=1.2, recovery=2.0):
        if not 0 < letter_gap < word_gap: raise ValueError('Word gap must be longer than letter gap')
        self.letter_gap, self.word_gap, self.long_breath, self.recovery = letter_gap, word_gap, long_breath, recovery
        self.reset()
    def reset(self):
        self.current='SILENCE'; self.duration=0.; self.silence=0.; self.code=''; self.word_done=True
        self.recovering=False; self.recovery_left=0.; self.recovery_wait_silence=False
    def advance(self, state, dt=.05):
        events=[]
        if self.recovering:
            # Ignore all breaths; start the comfort interval on the first silence.
            if self.recovery_wait_silence:
                if state != 'SILENCE': return events
                self.recovery_wait_silence=False
            self.recovery_left=max(0.,self.recovery_left-dt)
            if self.recovery_left<=0 and state=='SILENCE':
                self.recovering=False; self.current='SILENCE'; self.silence=0
                events.append(('ready',None))
            return events
        if state != self.current:
            if self.current in ('INHALE','EXHALE'):
                digit='1' if self.current=='INHALE' else '2'
                if len(self.code)<4:
                    self.code+=digit; events.append(('digit',self.code))
                else: events.append(('invalid',self.code+digit))
                self.word_done=False
            self.current=state; self.duration=0.
            if state!='SILENCE': self.silence=0.
        if state=='SILENCE':
            self.silence+=dt
            if self.code and self.silence>=self.letter_gap:
                events.append(('letter',CODES[self.code])); self.code=''
            if not self.word_done and self.silence>=self.word_gap:
                events.append(('space',None)); self.word_done=True
        else:
            self.duration+=dt
            if self.duration + 1e-9 >= self.long_breath:
                if self.current=='EXHALE' and self.code:
                    events.append(('letter',CODES[self.code]))
                events.append(('delete' if self.current=='INHALE' else 'send',None))
                self.code=''; self.recovering=True; self.recovery_left=self.recovery
                self.recovery_wait_silence=True; self.duration=0.
        return events
