"""Decode classified breath events and timed silence into text commands."""

CODES = dict(zip(
    ['1', '2', '11', '12', '21', '22', '111', '112', '121', '122',
     '211', '212', '221', '222', '1111', '1112', '1121', '1122',
     '1211', '1212', '1221', '1222', '2111', '2112', '2121', '2122'],
    'ETAOINSHRDLUCMFWGYPBVKJXQZ',
))
DELETE_CODE = '2211'
MAX_CODE_LENGTH = 5


class Decoder:
    def __init__(self, letter_gap=.8, word_gap=2.0, send_gap=4.0):
        if not 0 < letter_gap < word_gap < send_gap:
            raise ValueError('Timing must satisfy 0 < letter gap < word gap < send gap')
        self.letter_gap = letter_gap
        self.word_gap = word_gap
        self.send_gap = send_gap
        self.reset()

    def reset(self):
        self.current = 'SILENCE'
        self.silence = 0.0
        self.code = ''
        self.overflow = False
        self.word_pending = False
        self.send_armed = False

    def advance(self, state, dt=.05):
        """Consume one classified window, returning events in chronological order.

        Time is measured from classified silence, not the user's actual breath.
        A send is emitted at most once until a further code is committed.
        """
        if state not in ('SILENCE', 'INHALE', 'EXHALE') or dt <= 0:
            raise ValueError('Expected a positive-duration classified breath window')
        events = []
        if state != self.current:
            if self.current in ('INHALE', 'EXHALE'):
                if len(self.code) < MAX_CODE_LENGTH:
                    self.code += '1' if self.current == 'INHALE' else '2'
                    events.append(('digit', self.code))
                elif not self.overflow:
                    # Do not turn a long sequence into a truncated valid code.
                    self.overflow = True
                    self.word_pending = False
                    self.send_armed = False
                    events.append(('overflow', None))
            self.current = state
            if state != 'SILENCE':
                self.silence = 0.0

        if state != 'SILENCE':
            return events

        self.silence += dt
        epsilon = 1e-9
        if self.code and self.silence + epsilon >= self.letter_gap:
            code, self.code = self.code, ''
            overflow, self.overflow = self.overflow, False
            if overflow:
                events.append(('invalid', code))
                self.word_pending = False
                self.send_armed = False
            elif code == DELETE_CODE:
                events.append(('delete', None))
                # Deletion must not automatically put back a trailing space.
                self.word_pending = False
                self.send_armed = True
            elif code in CODES:
                events.append(('letter', CODES[code]))
                self.word_pending = True
                self.send_armed = True
            else:
                events.append(('invalid', code))
                self.word_pending = False
                self.send_armed = False

        if self.word_pending and self.silence + epsilon >= self.word_gap:
            events.append(('space', None))
            self.word_pending = False

        if self.send_armed and self.silence + epsilon >= self.send_gap:
            events.append(('send', None))
            self.send_armed = False

        return events
