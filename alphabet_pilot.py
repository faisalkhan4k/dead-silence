"""A separate letter dataset using the existing command-pilot capture workflow."""
import random
import json
import string
from pathlib import Path

from PySide6 import QtCore, QtWidgets as Q
from alphabet_models import freeze_training, evaluate_frozen
from dataset_pilot import CONFIG, Pilot

LETTERS = list(string.ascii_uppercase)
NAMES = dict(zip(LETTERS, ['ay', 'bee', 'see', 'dee', 'ee', 'ef', 'jee', 'aych', 'eye', 'jay',
                         'kay', 'el', 'em', 'en', 'oh', 'pee', 'cue', 'ar', 'ess', 'tee',
                         'you', 'vee', 'double-you', 'ex', 'why', 'zee']))
ALPHABET_ROOT = Path(__file__).resolve().parent/'alphabet_dataset'
GROUP_MAPPING = json.loads((Path(__file__).resolve().parent/'mappings'/'letter_names_9_v1.json').read_text(encoding='utf-8'))
ALPHABET_CONFIG = dict(CONFIG, task='alphabet', labels=LETTERS, pronunciation='English letter names; Z=zee',
                       train_per_letter=10, test_per_letter=5, block_size=26, experiment_version=1,
                       models=['SVM', 'RandomForest', 'LightGBM'], group_mapping=GROUP_MAPPING)


class ModelWorker(QtCore.QThread):
    succeeded = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, project, role, parent):
        super().__init__(parent)
        self.project, self.role = project, role
        self.config, self.labels = parent.config, parent.labels

    def run(self):
        try:
            operation = freeze_training if self.role == 'train' else evaluate_frozen
            self.succeeded.emit(operation(self.project, self.config, self.labels))
        except Exception as error:
            self.failed.emit(str(error))


class AlphabetPilot(Pilot):
    def __init__(self, labels=LETTERS, root=ALPHABET_ROOT, config=ALPHABET_CONFIG, block_size=26):
        super().__init__(labels=labels, root=root, config=config, block_size=block_size)
        self.worker = None
        self.setWindowTitle('Wired headset • alphabet dataset')
        self.prompt.setText('A–Z letter names • 10 training blocks, then 5 test blocks\nStart with reception check')
        self.counter.setText('Each block has 26 four-second trials. Take breaks between blocks. Z is “zee”.')
        self.start.setText('2. Record next training block')
        self.notes.setPlaceholderText('Keep your chosen system volume fixed; record volume, gain and placement')

    def make_order(self, count, seed):
        rng = random.Random(seed)
        order = []
        for _ in range(count):
            block = self.labels.copy()
            rng.shuffle(block)
            # Every block is balanced and boundaries do not repeat a letter.
            if order and order[-1] == block[0]:
                block[0], block[1] = block[1], block[0]
            order.extend(block)
        return order

    def action_prompt(self, label):
        return f'Silently say the letter name “{NAMES[label]}” once'

    def complete_session(self):
        if self.worker is not None and self.worker.isRunning():
            return
        self.controls(True)
        self.stop.setEnabled(False)
        self.prompt.setText('Training the three acoustic baselines…' if self.role == 'train' else 'Evaluating frozen models…')
        self.worker = ModelWorker(self.project, self.role, self)
        self.worker.succeeded.connect(self.models_finished)
        self.worker.failed.connect(self.models_failed)
        self.worker.start()

    def models_finished(self, result):
        self.controls(False)
        self.stop.setEnabled(True)
        if self.role == 'train':
            self.role, self.accepted, self.check_passed = 'test', {}, False
            self.confirm.setChecked(False)
            self.start.setText('2. Record next test block')
            self.prompt.setText('Training complete. Models frozen.\nReposition the headset, confirm setup and check reception before test collection.')
            self.status.setText('Saved training results and README in '+str(self.project))
        else:
            self.start.setEnabled(False)
            if self.config.get('group_mapping'):
                groups = json.loads((self.project/'grouped_evaluation.json').read_text(encoding='utf-8'))
                self.prompt.setText('\n'.join(f'{name} • letters {value["accuracy"]:.1%} • grouped {groups[name]["accuracy"]:.1%}' for name,value in result.items()))
            else:
                self.prompt.setText('\n'.join(f'{name} • held-out accuracy {value["accuracy"]:.1%}' for name,value in result.items()))
            self.status.setText('Saved evaluation, probability CSVs and README in '+str(self.project))

    def models_failed(self, error):
        self.controls(False)
        self.stop.setEnabled(True)
        self.prompt.setText('Model operation failed. Recordings are saved.')
        self.status.setText(error)

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            self.status.setText('Wait for the current model operation to finish before closing.')
            event.ignore()
            return
        super().closeEvent(event)


if __name__ == '__main__':
    app = Q.QApplication([])
    window = AlphabetPilot()
    window.show()
    app.exec()
