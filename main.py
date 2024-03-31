import mido


class MidiController:
    def __init__(self, out_port, in_port):
        self.notes_pressed = []
        self.out_port = out_port
        self.in_port = in_port

    def parse_midi(self, msg):
        if msg.type == 'clock':
            return
        if msg.type == 'note_on':
            self.notes_pressed.append(msg.note)
        elif msg.type == 'note_off':
            if msg.note in self.notes_pressed:
                self.notes_pressed.remove(msg.note)
            self.out_port.send(msg)
        if msg.type == 'note_on' or msg.type == 'note_off':
            self.handle_notes()

    def handle_notes(self):
        if self.notes_pressed:
            if len(self.notes_pressed) == 1:
                self.enable_osc2(False)
                self.start_note_normally(self.notes_pressed[-1])
            else:
                low_note = min(self.notes_pressed)
                other_notes = [note for note in self.notes_pressed if note != low_note]
                high_note = other_notes[-1]
                self.enable_osc2(True)
                self.prime_note_on_osc2(high_note, low_note)
                self.start_note_normally(low_note)

    def start_note_normally(self, note):
        self.out_port.send(mido.Message('note_on', note=note, velocity=127))

    def prime_note_on_osc2(self, note, main_note):
        semitone_diff = note - main_note
        octave_diff = 0

        if abs(semitone_diff) > 12:
            octave_diff = semitone_diff // 12
            semitone_diff = semitone_diff % 12

        if semitone_diff == 0:
            cv = 64
        elif semitone_diff > 0:
            if semitone_diff == 1:
                cv = 83
            else:
                cv = 83 + 4 * (semitone_diff - 1)
        else:
            if semitone_diff == -1:
                cv = 44
            else:
                cv = 44 + 4 * (semitone_diff + 1)

        self.out_port.send(mido.Message('control_change', control=35, value=cv))

        octave_dict = {-1: 0, 0: 42, 1: 84, 2: 127}
        self.out_port.send(mido.Message('control_change', control=49, value=octave_dict.get(octave_diff, 42)))

    def enable_osc2(self, on: bool):
        if on:
            self.out_port.send(mido.Message('control_change', control=40, value=127))
        else:
            self.out_port.send(mido.Message('control_change', control=40, value=0))

    def run(self):
        for msg in self.in_port:
            self.parse_midi(msg)


if __name__ == '__main__':
    out_port = mido.open_output('monologue SOUND')
    in_port = mido.open_input('monologue KBD/KNOB')
    controller = MidiController(out_port, in_port)
    controller.run()
