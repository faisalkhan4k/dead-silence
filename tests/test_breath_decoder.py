import unittest

from breath_decoder import CODES, DELETE_CODE, Decoder


def feed_code(decoder, code):
    events = []
    for digit in code:
        events += decoder.advance('INHALE' if digit == '1' else 'EXHALE', .1)
        events += decoder.advance('SILENCE', .05)
    return events


def advance_silence(decoder, seconds):
    events = []
    for _ in range(round(seconds / .05)):
        events += decoder.advance('SILENCE', .05)
    return events


class SilenceControlTests(unittest.TestCase):
    def test_every_letter_and_reserved_delete_have_unique_codes(self):
        self.assertEqual(len(CODES), 26)
        self.assertEqual(set(CODES.values()), set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        self.assertNotIn(DELETE_CODE, CODES)
        for code, letter in CODES.items():
            decoder = Decoder()
            events = feed_code(decoder, code) + advance_silence(decoder, .75)
            self.assertIn(('letter', letter), events, code)

    def test_one_pause_emits_letter_space_and_send_once(self):
        decoder = Decoder()
        events = feed_code(decoder, '1')
        events += advance_silence(decoder, .75)
        self.assertIn(('letter', 'E'), events)
        self.assertNotIn(('space', None), events)
        self.assertEqual(advance_silence(decoder, 1.2), [('space', None)])
        self.assertEqual(advance_silence(decoder, 2), [('send', None)])
        self.assertEqual(advance_silence(decoder, 8), [])

    def test_breath_restarts_send_countdown(self):
        decoder = Decoder()
        feed_code(decoder, '1')
        advance_silence(decoder, 3.85)
        feed_code(decoder, '2')
        events = advance_silence(decoder, 3.9)
        self.assertNotIn(('send', None), events)
        self.assertIn(('send', None), advance_silence(decoder, .05))

    def test_delete_is_a_code_and_does_not_add_a_word_space(self):
        decoder = Decoder()
        events = feed_code(decoder, DELETE_CODE) + advance_silence(decoder, 3.95)
        self.assertEqual([event for event in events if event[0] == 'delete'], [('delete', None)])
        self.assertFalse(any(event[0] in ('letter', 'space') for event in events))
        self.assertEqual([event for event in events if event[0] == 'send'], [('send', None)])

    def test_long_breath_does_not_trigger_a_command(self):
        decoder = Decoder()
        for _ in range(100):
            self.assertEqual(decoder.advance('EXHALE'), [])
        events = decoder.advance('SILENCE') + advance_silence(decoder, .75)
        self.assertIn(('letter', 'T'), events)
        self.assertFalse(any(event[0] in ('send', 'delete') for event in events))

    def test_unassigned_or_overlong_code_is_not_misread(self):
        for code in ('2212', '11111'):
            decoder = Decoder()
            events = feed_code(decoder, code) + advance_silence(decoder, .75)
            self.assertIn(('invalid', code), events)
            self.assertFalse(any(event[0] in ('letter', 'delete', 'space', 'send') for event in events))

    def test_invalid_code_disarms_automatic_send(self):
        decoder = Decoder()
        feed_code(decoder, '1')
        advance_silence(decoder, .75)
        events = feed_code(decoder, '2212') + advance_silence(decoder, 5)
        self.assertIn(('invalid', '2212'), events)
        self.assertNotIn(('send', None), events)

    def test_invalid_timing_and_initial_silence(self):
        for kwargs in ({'letter_gap': 2, 'word_gap': 2}, {'word_gap': 4, 'send_gap': 4}, {'letter_gap': 0}):
            with self.assertRaises(ValueError):
                Decoder(**kwargs)
        self.assertEqual(advance_silence(Decoder(), 10), [])


if __name__ == '__main__':
    unittest.main()
