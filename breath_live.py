"""Experimental 50 ms breath classifier with silence-based text controls."""
import json, os, pickle, queue, time
from pathlib import Path
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from PySide6 import QtCore, QtWidgets as Q
from breath_decoder import CODES, DELETE_CODE, Decoder
import breath_language
import re
import html
from difflib import SequenceMatcher


APP_STYLE = """
QWidget { background: #101722; color: #e6edf6; font-family: 'Segoe UI'; font-size: 12px; }
QLabel#brand { color: #f3f6fb; font-size: 23px; font-weight: 700; letter-spacing: 2px; }
QLabel#tagline, QLabel#keyboardTitle { color: #93a3b9; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#keyboardLegend { color: #b4c1d0; font-size: 11px; }
QLabel#keyboardLetter { background: transparent; color: #f3f6fb; font-size: 16px; font-weight: 700; }
QLabel#keyboardCode { background: transparent; color: #ff626d; font-family: Consolas; font-size: 12px; font-weight: 700; }
QPlainTextEdit, QLineEdit, QComboBox, QDoubleSpinBox { background: #1a2533; border: 1px solid #334457; border-radius: 7px; padding: 6px 8px; selection-background-color: #326684; }
QPlainTextEdit#messageBox { color: #f4f7fb; font-size: 21px; padding: 12px; border: 1px solid #3a4d60; }
QComboBox QAbstractItemView { background: #1a2533; color: #e6edf6; selection-background-color: #34526c; }
QPushButton { background: #253448; border: 1px solid #3a5069; border-radius: 7px; padding: 7px 12px; color: #e6edf6; font-weight: 600; }
QPushButton:hover { background: #30465e; }
QPushButton:disabled { color: #718094; background: #1a2533; border-color: #273546; }
QPushButton#primaryButton { background: #315b76; border-color: #477c9a; color: #ffffff; }
QPushButton#primaryButton:hover { background: #3c6d8a; }
QFrame#keyboardPanel { background: #17212e; border: 1px solid #2d3b4d; border-radius: 10px; }
QFrame#keyboardPanel QLabel { background: transparent; }
QFrame#keyboardKey { background: #233244; border: 1px solid #40526a; border-radius: 7px; }
"""

HERE = Path(__file__).resolve().parent
def find_dataset():
    root = HERE/'breath_dataset'
    runs = sorted((p for p in root.glob('*') if p.is_dir() and (p/'train_accepted.json').exists() and (p/'test_accepted.json').exists()), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        raise SystemExit('No complete breath dataset found. Run Start Breath Dataset.cmd first and complete training and test collection.')
    return runs[0]
DATA = find_dataset()
BASELINE_MODEL = DATA/'window50_model.pkl'
NOISY_MODEL = HERE/'breath_noise_dataset'/'active_model.pkl'
# Use the initial 50 ms model; newer noise-trained checkpoints remain experimental.
MODEL = BASELINE_MODEL
RATE, N = 48000, 2400
LABELS = ['SILENCE', 'INHALE', 'EXHALE']

def feature(x):
    x = np.asarray(x, dtype=float)
    if len(x) != N: raise ValueError('Expected 50 ms at 48 kHz')
    spectrum = abs(np.fft.rfft(x*np.hanning(N)))**2 / N**2
    f = np.fft.rfftfreq(N, 1/RATE)
    bands = [(80,300),(300,700),(700,1500),(1500,3000),(3000,6000),(6000,12000)]
    return np.array([np.log10(np.mean(spectrum[(f>=a)&(f<b)])+1e-12) for a,b in bands])

def examples(role):
    rows = json.loads((DATA/f'{role}_accepted.json').read_text())
    X,y = [],[]
    for row in rows.values():
        rate, x = wavfile.read(row['path'])
        if rate != RATE or len(x) != 4*RATE: raise ValueError('Unexpected recording format')
        if np.issubdtype(x.dtype, np.integer): x=x.astype(float)/np.iinfo(x.dtype).max
        for start in range(int(.15*RATE), int(.85*RATE), N):
            X.append(feature(x[start:start+N])); y.append('SILENCE')
        # Weak labels: action cue does not mean every 50 ms contains breathing.
        for start in range(int(1.1*RATE), int(2.9*RATE), N):
            X.append(feature(x[start:start+N])); y.append(row['label'])
    return np.array(X),np.array(y)

def train():
    X,y=examples('train'); T,t=examples('test')
    model=RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=4, random_state=42, n_jobs=1, class_weight='balanced')
    model.fit(X,y); pred=model.predict(T)
    MODEL.write_bytes(pickle.dumps(model))
    result={'window_accuracy_weak_labels':float(accuracy_score(t,pred)), 'labels':LABELS,
            'confusion_matrix':confusion_matrix(t,pred,labels=LABELS).tolist(), 'test_windows':len(t)}
    (DATA/'window50_evaluation.json').write_text(json.dumps(result,indent=2))
    try:
        import mlflow
        mlflow.set_tracking_uri('sqlite:///'+(HERE/'breath_mlflow.db').as_posix())
        mlflow.set_experiment('breath-live')
        with mlflow.start_run(run_name='50ms-window-training'):
            mlflow.log_params({'window_ms':50,'model':'random_forest','labels':'weak action-window labels','test_split':'held-out recordings'})
            mlflow.log_metric('weak_window_accuracy',result['window_accuracy_weak_labels'])
            mlflow.log_artifact(str(DATA/'window50_evaluation.json'))
    except Exception as e: print(f'MLflow logging unavailable: {e}')
    print(json.dumps(result,indent=2))

class Worker(QtCore.QThread):
    done = QtCore.Signal(str, object, str)
    def __init__(self, kind, text):
        super().__init__(); self.kind=kind; self.text=text
    def run(self):
        try:
            fn={'suggest':breath_language.suggestions, 'respond':breath_language.respond, 'speak':breath_language.speak}[self.kind]
            self.done.emit(self.kind, fn(self.text), '')
        except Exception as exc: self.done.emit(self.kind, None, str(exc))

class Window(Q.QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Breath to text • noise-trained' if MODEL == NOISY_MODEL else 'Breath to text • pre-marker 50 ms model')
        self.resize(1420,920); self.setMinimumSize(1000,650)
        self.setStyleSheet(APP_STYLE)
        self.model=pickle.loads(MODEL.read_bytes()); self.q=queue.Queue(maxsize=50)
        self.stream=None; self.times=[]; self.drops=0; self.workers=[]; self.speaking=False
        self.suggestion_source=None; self.suggestion_word=None
        self.current='SILENCE'; self.candidate='SILENCE'; self.count=0; self.decoder=Decoder()
        root=Q.QVBoxLayout(self); root.setContentsMargins(22,18,22,18); root.setSpacing(12)
        scroll=Q.QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(Q.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_content=Q.QWidget(); main_content.setMinimumHeight(570)
        layout=Q.QVBoxLayout(main_content); layout.setContentsMargins(0,0,0,0); layout.setSpacing(9)
        scroll.setWidget(main_content); root.addWidget(scroll,1)
        header=Q.QHBoxLayout()
        brand=Q.QLabel('DEAD SILENCE'); brand.setObjectName('brand')
        tagline=Q.QLabel('BREATH TO TEXT'); tagline.setObjectName('tagline')
        header.addWidget(brand); header.addWidget(tagline); header.addStretch()
        layout.addLayout(header)
        self.devices=[(i,d) for i,d in enumerate(sd.query_devices()) if d['max_input_channels']]
        self.device=Q.QComboBox()
        for i,d in self.devices: self.device.addItem(d['name'],i)
        layout.addWidget(self.device)
        key_row=Q.QHBoxLayout(); layout.addLayout(key_row)
        self.key_input=Q.QLineEdit(); self.key_input.setEchoMode(Q.QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText('Gemini API key (optional if GEMINI_API_KEY is in .env)')
        key_row.addWidget(self.key_input)
        key_button=Q.QPushButton('Use key for this session'); key_button.clicked.connect(self.set_key); key_row.addWidget(key_button)
        self.info=Q.QLabel(f'1 = inhale • 2 = exhale • five breaths per letter • {DELETE_CODE} = delete'); self.info.setWordWrap(True); layout.addWidget(self.info)
        self.live=Q.QLabel('Ready'); self.live.setStyleSheet('font-size: 24px; font-weight: bold'); layout.addWidget(self.live)
        self.target=Q.QLineEdit(); self.target.setPlaceholderText('Optional experiment target phrase (not sent to MLflow)'); layout.addWidget(self.target)
        self.message=Q.QPlainTextEdit(); self.message.setPlaceholderText('Decoded text appears here. You can edit it.')
        self.message.setObjectName('messageBox'); self.message.setMinimumHeight(90); layout.addWidget(self.message,1)
        comfort=Q.QHBoxLayout(); layout.addLayout(comfort); comfort.addWidget(Q.QLabel('Comfort after this run:'))
        self.comfort=Q.QComboBox(); self.comfort.addItems(['Not rated','1 - very uncomfortable','2 - uncomfortable','3 - neutral','4 - comfortable','5 - very comfortable']); comfort.addWidget(self.comfort)
        self.ghost=Q.QLabel(''); self.ghost.setWordWrap(True); self.ghost.setTextFormat(QtCore.Qt.TextFormat.RichText); layout.addWidget(self.ghost)
        self.suggestions=Q.QHBoxLayout(); layout.addLayout(self.suggestions)
        self.suggestion_buttons=[]
        for _ in range(3):
            button=Q.QPushButton('—'); button.setEnabled(False); button.clicked.connect(lambda checked=False,b=button:self.use_suggestion(b.text()))
            self.suggestions.addWidget(button); self.suggestion_buttons.append(button)
        self.language_status=Q.QLabel('Gemini is configured for suggestions and replies.' if os.environ.get('GEMINI_API_KEY', '').strip() else 'Add GEMINI_API_KEY to .env, then restart.'); self.language_status.setWordWrap(True); layout.addWidget(self.language_status)
        self.reply=Q.QLabel('Crewmate reply: —'); self.reply.setWordWrap(True); layout.addWidget(self.reply)
        opts=Q.QHBoxLayout(); layout.addLayout(opts)
        self.letter_gap=self.spin(opts,'Between letters',.3,3,.8)
        self.word_gap=self.spin(opts,'Word gap',.5,8,2)
        self.send_gap=self.spin(opts,'Send gap',1,15,4)
        buttons=Q.QHBoxLayout(); layout.addLayout(buttons)
        self.start=Q.QPushButton('Start'); self.start.setObjectName('primaryButton'); self.start.clicked.connect(self.toggle); buttons.addWidget(self.start)
        send=Q.QPushButton('Send'); send.clicked.connect(self.send); buttons.addWidget(send)
        delete=Q.QPushButton('Delete letter'); delete.clicked.connect(self.delete_letter); buttons.addWidget(delete)
        space=Q.QPushButton('Space'); space.clicked.connect(lambda:self.insert(' ')); buttons.addWidget(space)
        root.addWidget(self.build_reference_panel())
        self.timer=QtCore.QTimer(self); self.timer.timeout.connect(self.poll); self.timer.start(25)
        self.suggest_timer=QtCore.QTimer(self); self.suggest_timer.setSingleShot(True); self.suggest_timer.timeout.connect(self.request_suggestions)
        self.message.textChanged.connect(self.text_changed)
    def build_reference_panel(self):
        panel=Q.QFrame(); panel.setObjectName('keyboardPanel')
        layout=Q.QVBoxLayout(panel); layout.setContentsMargins(14,11,14,12); layout.setSpacing(7)
        title=Q.QHBoxLayout()
        heading=Q.QLabel('BREATH-CODE KEYBOARD'); heading.setObjectName('keyboardTitle')
        legend=Q.QLabel('INHALE  1     ·     EXHALE  2     ·     DELETE  ' + DELETE_CODE)
        legend.setObjectName('keyboardLegend')
        title.addWidget(heading); title.addStretch(); title.addWidget(legend)
        layout.addLayout(title)
        by_letter={letter:code for code,letter in CODES.items()}
        self.reference_codes=dict(CODES)
        self.keyboard_keys={}
        for row_index,letters in enumerate(('QWERTYUIOP','ASDFGHJKL','ZXCVBNM')):
            row=Q.QHBoxLayout(); row.setSpacing(6)
            if row_index: row.addSpacing(22 if row_index==1 else 65)
            for letter in letters:
                frame=Q.QFrame(); frame.setObjectName('keyboardKey'); frame.setMinimumHeight(46)
                frame.setSizePolicy(Q.QSizePolicy.Policy.Expanding,Q.QSizePolicy.Policy.Fixed)
                contents=Q.QVBoxLayout(frame); contents.setContentsMargins(4,3,4,3); contents.setSpacing(0)
                name=Q.QLabel(letter); name.setObjectName('keyboardLetter'); name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                code=Q.QLabel(by_letter[letter]); code.setObjectName('keyboardCode'); code.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                contents.addWidget(name); contents.addWidget(code)
                self.keyboard_keys[letter]=code
                row.addWidget(frame,1)
            if row_index: row.addSpacing(22 if row_index==1 else 65)
            layout.addLayout(row)
        return panel
    def text_changed(self):
        self.suggestion_source=None; self.suggestion_word=None; self.ghost.clear()
        for button in self.suggestion_buttons: button.setEnabled(False); button.setText('—')
        self.suggest_timer.start(150)
    def show_ghost(self, text, word):
        prefix=re.search(r'[A-Za-z]+$',text)
        if prefix and word.lower().startswith(prefix.group().lower()) and len(word)>len(prefix.group()):
            tail=word[len(prefix.group()):]
            self.ghost.setText('<span>Completion: '+html.escape(prefix.group())+'</span><span style="color:#999;">'+html.escape(tail)+'</span>')
        else: self.ghost.clear()
    def accept_word_pause(self):
        text=self.message.toPlainText()
        prefix=re.search(r'[A-Za-z]+$',text)
        if prefix and self.suggestion_source==text and self.suggestion_word:
            self.use_suggestion(self.suggestion_word)
        elif text and not text.endswith(' '): self.insert(' ')
    def set_key(self):
        key=self.key_input.text().strip()
        if key:
            os.environ['GEMINI_API_KEY']=key; self.key_input.clear()
            self.language_status.setText('Key set for this app session. Text is sent to Gemini for suggestions and replies.'); self.suggest_timer.start(300)
        else: self.language_status.setText('Enter an API key first.')
    def spin(self, layout, label, low, high, value):
        layout.addWidget(Q.QLabel(label+' (s)')); spin=Q.QDoubleSpinBox(); spin.setRange(low,high); spin.setSingleStep(.1); spin.setValue(value); layout.addWidget(spin); return spin
    def insert(self,text):
        cursor=self.message.textCursor(); cursor.movePosition(cursor.MoveOperation.End); cursor.insertText(text); self.message.setTextCursor(cursor)
    def delete_letter(self):
        text=self.message.toPlainText().rstrip(); self.message.setPlainText(text[:-1]); self.decoder.code=''
    def use_suggestion(self,word):
        text=self.message.toPlainText(); prefix=re.search(r'[A-Za-z]+$',text)
        if prefix: text=text[:prefix.start()]
        self.message.setPlainText(text+word+' ')
    def launch_worker(self,kind,text):
        if any(w.isRunning() and w.kind==kind for w in self.workers): return False
        w=Worker(kind,text); self.workers.append(w); w.done.connect(lambda k,r,e,w=w:self.worker_done(w,k,r,e)); w.finished.connect(lambda w=w:self.workers.remove(w) if w in self.workers else None); w.start(); return True
    def request_suggestions(self):
        text=self.message.toPlainText()
        for b in self.suggestion_buttons: b.setEnabled(False); b.setText('—')
        if text.strip() and not self.speaking:
            if self.launch_worker('suggest',text):
                self.language_status.setText('Asking Gemini for a suggestion…')
            else:
                self.language_status.setText('Waiting for the previous suggestion…')
    def worker_done(self,worker,kind,result,error):
        if kind=='suggest':
            if worker.text!=self.message.toPlainText(): self.suggest_timer.start(300); return
            if error: self.language_status.setText('Suggestions unavailable: ' + error + ''); return
            prefix=re.search(r'[A-Za-z]+$',worker.text); prefix=prefix.group().lower() if prefix else ''
            words=[]
            for line in result.splitlines():
                word=line.strip().strip(' -0123456789.)')
                if re.fullmatch(r'[A-Za-z]+',word) and word.lower().startswith(prefix) and word.lower() not in [x.lower() for x in words]: words.append(word)
            for b,word in zip(self.suggestion_buttons,words[:3]): b.setText(word); b.setEnabled(True)
            if words:
                self.suggestion_source=worker.text; self.suggestion_word=words[0]
                self.show_ghost(worker.text,words[0])
            if words:
                self.language_status.setText('Gemini suggestions ready; the word pause accepts the shown completion.')
            else:
                self.language_status.setText('No matching suggestion yet; try another letter.')
        elif kind=='respond':
            if error:
                self.language_status.setText('Gemini unavailable. Speaking the original message; no cleanup or generated reply. ' + error + '')
                self.reply.setText('Crewmate reply unavailable'); spoken=worker.text
            else:
                cleaned,reply=result; self.message.setPlainText(cleaned); self.reply.setText('Crewmate reply: '+reply); spoken=reply
                self.language_status.setText('Message cleaned and reply generated by Gemini.')
            self.speaking=True; self.launch_worker('speak',spoken)
        elif kind=='speak':
            self.speaking=False; self.current=self.candidate='SILENCE'; self.count=0
            # Do not decode samples buffered while the spoken reply was playing.
            for _ in range(self.q.maxsize):
                try: self.q.get_nowait()
                except queue.Empty: break
            self.decoder.reset()
            self.info.setText('Ready for the next input.')
            if error: self.language_status.setText('Speech failed: '+error)
    def send(self):
        text=self.message.toPlainText().strip()
        if not text: self.info.setText('Nothing to send.'); return
        if self.launch_worker('respond',text):
            self.speaking=True; self.reply.setText('Crewmate is thinking…'); self.info.setText('Input paused while the crewmate responds and speaks.')
    def callback(self,data,frames,timing,status):
        if status: self.drops+=1
        try: self.q.put_nowait((data[:,0].copy(),time.perf_counter()))
        except queue.Full: self.drops+=1
    def toggle(self):
        if self.stream: self.stop(); return
        if not self.letter_gap.value() < self.word_gap.value() < self.send_gap.value():
            self.info.setText('Set the gaps in increasing order: letter < word < send.'); return
        self.decoder=Decoder(self.letter_gap.value(),self.word_gap.value(),self.send_gap.value())
        self.current=self.candidate='SILENCE'; self.count=0
        self.run_target=self.target.text(); self.run_started=time.perf_counter()
        try:
            self.stream=sd.InputStream(device=self.device.currentData(),samplerate=RATE,channels=1,dtype='float32',blocksize=N,callback=self.callback)
            self.stream.start(); self.device.setEnabled(False); self.start.setText('Stop and log')
            for control in (self.letter_gap,self.word_gap,self.send_gap): control.setEnabled(False)
        except Exception as e:
            if self.stream: self.stream.close(); self.stream=None
            self.info.setText(str(e))
    def poll(self):
        for _ in range(20):
            try: x,arrival=self.q.get_nowait()
            except queue.Empty: break
            if len(x)!=N: self.drops+=1; continue
            if self.speaking: continue
            t=time.perf_counter(); label=str(self.model.predict(feature(x).reshape(1,-1))[0]); elapsed=(time.perf_counter()-t)*1000
            self.times.append((elapsed,(time.perf_counter()-arrival)*1000))
            if label==self.candidate: self.count+=1
            else: self.candidate=label; self.count=1
            if self.count>=3: self.current=label
            for event,value in self.decoder.advance(self.current):
                if event=='letter': self.insert(value)
                elif event=='space': self.accept_word_pause()
                elif event=='delete': self.delete_letter(); self.info.setText('Deleted last letter.')
                elif event=='send': self.info.setText('Send pause reached.'); self.send()
                elif event=='invalid': self.info.setText(f'Unassigned code {value}; try again.')
                elif event=='incomplete': self.info.setText(f'Incomplete code {value}; enter all five breaths.')
                elif event=='overflow': self.info.setText('Maximum 5 numbers; pause and try again.')
            countdown = ''
            if (self.current=='SILENCE' and self.decoder.send_armed
                    and self.decoder.silence >= self.decoder.word_gap):
                countdown = f'  |  send in {max(0., self.decoder.send_gap-self.decoder.silence):.1f} s'
            self.live.setText(f'{self.current}  |  code: {self.decoder.code or "—"}  |  compute {elapsed:.1f} ms{countdown}')
    def stop(self):
        self.stream.stop(); self.stream.close(); self.stream=None
        self.device.setEnabled(True); self.start.setText('Start')
        for control in (self.letter_gap,self.word_gap,self.send_gap): control.setEnabled(True)
        if self.times:
            arr=np.asarray(self.times); self.info.setText(f'Frames: {len(arr)}; compute median {np.median(arr[:,0]):.1f} ms, p95 {np.percentile(arr[:,0],95):.1f} ms; callback-to-result p95 {np.percentile(arr[:,1],95):.1f} ms; faults/drops {self.drops}.')
            try:
                import mlflow
                mlflow.set_tracking_uri('sqlite:///'+(HERE/'breath_mlflow.db').as_posix()); mlflow.set_experiment('breath-live')
                with mlflow.start_run(run_name='live-inference'):
                    mlflow.log_params({'window_ms':50,'smoothing_windows':3,'letter_gap_s':self.decoder.letter_gap,'word_gap_s':self.decoder.word_gap,'send_gap_s':self.decoder.send_gap,'control_mode':'silence_send_code_delete','model':'random_forest','model_variant':('noise_trained' if MODEL == NOISY_MODEL else 'original')})
                    metrics={'compute_p50_ms':float(np.median(arr[:,0])), 'compute_p95_ms':float(np.percentile(arr[:,0],95)), 'callback_to_result_p95_ms':float(np.percentile(arr[:,1],95)), 'frames':len(arr),'faults_or_drops':self.drops,'duration_s':time.perf_counter()-self.run_started}
                    target=self.run_target.strip().casefold(); actual=self.message.toPlainText().strip().casefold()
                    if target:
                        metrics.update(target_exact_match=float(actual==target), character_similarity=SequenceMatcher(None,target,actual).ratio(), target_characters=len(target), result_characters=len(actual))
                    if self.comfort.currentIndex(): metrics['comfort_rating_1_to_5']=self.comfort.currentIndex()
                    mlflow.log_metrics(metrics)
            except Exception as e: self.info.setText(self.info.text()+f' MLflow logging failed: {e}')
        self.times=[]; self.drops=0
    def closeEvent(self,event):
        if any(w.isRunning() for w in self.workers):
            self.info.setText('Wait for the language or speech operation to finish before closing.'); event.ignore(); return
        if self.stream: self.stop()
        event.accept()

if __name__=='__main__':
    import sys
    if '--train' in sys.argv: train()
    else:
        app=Q.QApplication([]); window=Window(); window.show(); app.exec()

