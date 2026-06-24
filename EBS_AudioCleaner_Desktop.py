# -*- coding: utf-8 -*-
"""
EBS Audio Cleaner Desktop
Video / ses dosyalarındaki dip ses, tıslama, uğultu ve röportaj arka plan gürültülerini azaltmak için Tkinter + FFmpeg masaüstü aracı.

Kurulum:
1) Python 3.10+ kurulu olsun.
2) FFmpeg kurulu olsun ve PATH'e ekli olsun. Test: ffmpeg -version
3) Çalıştır: python EBS_AudioCleaner_Desktop.py

Not: Arka plandaki başka insan konuşmalarını tamamen yok etmek, tek kanal kayıt varsa teknik olarak her zaman mümkün değildir.
Bu araç onları azaltmaya çalışır; en iyi sonuç için yaka mikrofonu / yönlü mikrofonla kaydedilmiş ana konuşma gerekir.
"""

import os
import sys
import shutil
import subprocess
import threading
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "EBS Audio Cleaner Desktop - Röportaj Ses Temizleme"

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}

PRESETS = {
    "Röportaj - Hafif Ortam": {
        "noise": 32, "hiss": 6200, "hum": 50, "speech": 3, "crowd": 22, "deess": 18, "gain": 100,
        "desc": "Hafif sokak/oda sesi. Konuşmayı doğal bırakır."
    },
    "Röportaj - Kalabalık İnsan Sesi": {
        "noise": 58, "hiss": 5200, "hum": 50, "speech": 5, "crowd": 65, "deess": 25, "gain": 105,
        "desc": "Arka plandaki insan uğultusunu azaltmayı dener; ana konuşma da biraz incelir."
    },
    "Fan / Klima Uğultusu": {
        "noise": 68, "hiss": 7000, "hum": 50, "speech": 3, "crowd": 15, "deess": 12, "gain": 100,
        "desc": "Sabit fan, klima, bilgisayar uğultusu için."
    },
    "Tıslama / Cızırtı": {
        "noise": 42, "hiss": 4200, "hum": 50, "speech": 2, "crowd": 8, "deess": 55, "gain": 100,
        "desc": "S, ş, cızırtı ve yüksek frekans rahatsızlığı için."
    },
    "Telefon / Haber Muhabiri": {
        "noise": 50, "hiss": 4800, "hum": 50, "speech": 6, "crowd": 40, "deess": 25, "gain": 112,
        "desc": "Konuşmayı öne alır, yayın/haber sesine yaklaştırır."
    },
    "Ağır Temizlik - Riskli": {
        "noise": 85, "hiss": 3600, "hum": 50, "speech": 6, "crowd": 85, "deess": 45, "gain": 110,
        "desc": "Çok gürültülü kayıtlar için. Ses robotik/boğuk olabilir."
    },
}

class AudioCleanerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x720")
        self.minsize(900, 640)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status = tk.StringVar(value="Hazır. Önce video veya ses dosyası seçin.")
        self.preset_name = tk.StringVar(value="Röportaj - Kalabalık İnsan Sesi")
        self.keep_video = tk.BooleanVar(value=True)
        self.use_rnnoise = tk.BooleanVar(value=False)
        self.rnnoise_model = tk.StringVar(value="")
        self.temp_dir = Path(tempfile.gettempdir()) / "ebs_audio_cleaner"
        self.temp_dir.mkdir(exist_ok=True)

        self.vars = {
            "noise": tk.IntVar(value=58),
            "hiss": tk.IntVar(value=5200),
            "hum": tk.IntVar(value=50),
            "speech": tk.IntVar(value=5),
            "crowd": tk.IntVar(value=65),
            "deess": tk.IntVar(value=25),
            "gain": tk.IntVar(value=105),
        }
        self._build_ui()
        self.apply_preset()
        self._check_ffmpeg()

    def _build_ui(self):
        self.configure(bg="#0b1020")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0b1020")
        style.configure("Card.TFrame", background="#141b2f", relief="flat")
        style.configure("TLabel", background="#0b1020", foreground="#eef2ff", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#f7d98b", background="#0b1020")
        style.configure("Small.TLabel", foreground="#aab4cf", background="#0b1020")
        style.configure("TButton", padding=8, font=("Segoe UI", 10, "bold"))
        style.configure("Horizontal.TScale", background="#141b2f")
        style.configure("TCheckbutton", background="#0b1020", foreground="#eef2ff")
        style.configure("TCombobox", fieldbackground="#111827", background="#111827", foreground="#fff")

        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="EBS Audio Cleaner Desktop", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Video/ses dosyasındaki dip ses, fan uğultusu, tıslama ve röportaj arka plan seslerini FFmpeg filtreleriyle azaltır.", style="Small.TLabel").pack(anchor="w", pady=(3, 16))

        file_card = ttk.Frame(root, style="Card.TFrame", padding=14)
        file_card.pack(fill="x", pady=(0, 12))

        row1 = ttk.Frame(file_card, style="Card.TFrame")
        row1.pack(fill="x")
        ttk.Label(row1, text="Giriş dosyası:", background="#141b2f").pack(side="left")
        ttk.Entry(row1, textvariable=self.input_path).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row1, text="Dosya Seç", command=self.choose_input).pack(side="left")

        row2 = ttk.Frame(file_card, style="Card.TFrame")
        row2.pack(fill="x", pady=(8, 0))
        ttk.Label(row2, text="Çıkış dosyası:", background="#141b2f").pack(side="left")
        ttk.Entry(row2, textvariable=self.output_path).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row2, text="Kaydet Yeri", command=self.choose_output).pack(side="left")

        preset_card = ttk.Frame(root, style="Card.TFrame", padding=14)
        preset_card.pack(fill="x", pady=(0, 12))
        ttk.Label(preset_card, text="Hazır filtre:", background="#141b2f").pack(side="left")
        cmb = ttk.Combobox(preset_card, textvariable=self.preset_name, values=list(PRESETS.keys()), state="readonly", width=34)
        cmb.pack(side="left", padx=8)
        cmb.bind("<<ComboboxSelected>>", lambda e: self.apply_preset())
        ttk.Button(preset_card, text="Preset Uygula", command=self.apply_preset).pack(side="left")
        self.preset_desc = ttk.Label(preset_card, text="", background="#141b2f", foreground="#aab4cf")
        self.preset_desc.pack(side="left", padx=12)

        sliders = ttk.Frame(root, style="Card.TFrame", padding=14)
        sliders.pack(fill="both", expand=True, pady=(0, 12))

        self._add_slider(sliders, "noise", "Gürültü Azaltma", 0, 100, "Dip ses / sabit ortam gürültüsü azaltma")
        self._add_slider(sliders, "hiss", "Tıslama Kesimi Hz", 2500, 11000, "Düşük değer daha çok tıslama keser, sesi boğabilir")
        self._add_slider(sliders, "hum", "Elektrik Uğultusu", 0, 60, "0 kapalı, 50 veya 60 Hz notch uygular")
        self._add_slider(sliders, "speech", "Konuşma Netliği", 0, 10, "2-5 kHz bandını öne alır")
        self._add_slider(sliders, "crowd", "Arka İnsan Sesi Bastırma", 0, 100, "Kalabalık mırıltısını azaltmayı dener; ana konuşmayı da etkileyebilir")
        self._add_slider(sliders, "deess", "S / Ş Patlama Azaltma", 0, 100, "6-9 kHz bölgesinde de-esser benzeri kontrol")
        self._add_slider(sliders, "gain", "Çıkış Sesi %", 50, 160, "İşlenen sesin genel seviyesi")

        options = ttk.Frame(root, style="Card.TFrame", padding=14)
        options.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(options, text="Video görüntüsünü koru, sadece sesi değiştir", variable=self.keep_video).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(options, text="RNNoise model kullan (isteğe bağlı .rnnn dosyası)", variable=self.use_rnnoise).pack(side="left")
        ttk.Entry(options, textvariable=self.rnnoise_model, width=38).pack(side="left", padx=8)
        ttk.Button(options, text="Model Seç", command=self.choose_model).pack(side="left")

        actions = ttk.Frame(root)
        actions.pack(fill="x")
        ttk.Button(actions, text="15 sn Önizleme Oluştur", command=self.preview_thread).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Tam Dosyayı Temizle", command=self.process_thread).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Filtre Komutunu Göster", command=self.show_command).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Çıkış Klasörünü Aç", command=self.open_output_folder).pack(side="left")

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", pady=(12, 6))
        ttk.Label(root, textvariable=self.status, style="Small.TLabel").pack(anchor="w")

    def _add_slider(self, parent, key, title, minv, maxv, help_text):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=6)
        label = ttk.Label(row, text=title, width=24, background="#141b2f")
        label.pack(side="left")
        scale = ttk.Scale(row, from_=minv, to=maxv, variable=self.vars[key], orient="horizontal")
        scale.pack(side="left", fill="x", expand=True, padx=8)
        val = ttk.Label(row, textvariable=self.vars[key], width=8, background="#141b2f", foreground="#f7d98b")
        val.pack(side="left")
        help_lbl = ttk.Label(row, text=help_text, width=44, background="#141b2f", foreground="#aab4cf")
        help_lbl.pack(side="left", padx=(8, 0))

    def _check_ffmpeg(self):
        if not shutil.which("ffmpeg"):
            self.status.set("FFmpeg bulunamadı. ffmpeg kurup PATH'e ekleyin. Windows: winget install Gyan.FFmpeg")
        elif not shutil.which("ffplay"):
            self.status.set("FFmpeg var, ffplay yok. Önizleme dosyası oluşturulur ama otomatik oynatma çalışmayabilir.")

    def choose_input(self):
        path = filedialog.askopenfilename(title="Video veya ses seç", filetypes=[("Medya Dosyaları", "*.mp4 *.mov *.mkv *.webm *.avi *.m4v *.wav *.mp3 *.m4a *.aac *.flac *.ogg *.opus"), ("Tüm Dosyalar", "*.*")])
        if path:
            self.input_path.set(path)
            p = Path(path)
            out = p.with_name(p.stem + "_temizlendi" + (p.suffix if p.suffix.lower() in VIDEO_EXTS else ".wav"))
            self.output_path.set(str(out))

    def choose_output(self):
        inp = Path(self.input_path.get()) if self.input_path.get() else Path("temizlendi.mp4")
        ext = inp.suffix if inp.suffix.lower() in VIDEO_EXTS else ".wav"
        path = filedialog.asksaveasfilename(title="Çıkış dosyası", defaultextension=ext, initialfile=inp.stem + "_temizlendi" + ext)
        if path:
            self.output_path.set(path)

    def choose_model(self):
        path = filedialog.askopenfilename(title="RNNoise model dosyası seç", filetypes=[("RNNoise model", "*.rnnn *.model"), ("Tüm Dosyalar", "*.*")])
        if path:
            self.rnnoise_model.set(path)
            self.use_rnnoise.set(True)

    def apply_preset(self):
        preset = PRESETS[self.preset_name.get()]
        for k, v in preset.items():
            if k in self.vars:
                self.vars[k].set(v)
        self.preset_desc.config(text=preset.get("desc", ""))

    def build_filter(self):
        noise = self.vars["noise"].get()
        hiss = self.vars["hiss"].get()
        hum = self.vars["hum"].get()
        speech = self.vars["speech"].get()
        crowd = self.vars["crowd"].get()
        deess = self.vars["deess"].get()
        gain = self.vars["gain"].get()

        filters = []
        # Röportaj için alt uğultu temizliği
        hp = int(35 + noise * 1.7)
        filters.append(f"highpass=f={hp}")

        # Elektrik uğultusu 50/60 Hz ve harmonikleri
        if hum in (50, 60):
            for f in (hum, hum*2, hum*3):
                filters.append(f"anequalizer=c0 f={f} w=8 g=-18")

        # Sabit gürültü azaltma: afftdn FFmpeg'in yaygın filtresidir.
        nr = round(4 + noise * 0.22, 1)  # 4-26 dB civarı
        nf = round(-22 - noise * 0.38, 1)
        filters.append(f"afftdn=nr={nr}:nf={nf}:tn=1")

        # İsteğe bağlı RNNoise / arnndn modeli
        model = self.rnnoise_model.get().strip()
        if self.use_rnnoise.get() and model and Path(model).exists():
            safe_model = model.replace('\\', '/').replace(':', '\\:')
            filters.append(f"arnndn=m='{safe_model}':mix=0.85")

        # Arka insan uğultusu azaltma: konuşma dışı bölgeleri daraltır, orta bandı kontrollü törpüler.
        if crowd > 0:
            low_cut = int(80 + crowd * 1.6)
            high_cut = int(max(3000, 9000 - crowd * 45))
            mid_dip = round(-(crowd / 100) * 5.5, 2)
            filters.append(f"highpass=f={low_cut}")
            filters.append(f"lowpass=f={high_cut}")
            filters.append(f"equalizer=f=900:t=q:w=1.4:g={mid_dip}")
            filters.append(f"equalizer=f=1400:t=q:w=1.2:g={mid_dip/1.4:.2f}")

        # Tıslama / S patlaması
        if deess > 0:
            ds = round(-(deess / 100) * 9, 2)
            filters.append(f"equalizer=f=6500:t=q:w=1.0:g={ds}")
            filters.append(f"equalizer=f=8500:t=q:w=1.1:g={ds/1.4:.2f}")

        # Genel tıslama kesimi ve konuşma netliği
        filters.append(f"lowpass=f={int(hiss)}")
        if speech > 0:
            filters.append(f"equalizer=f=2800:t=q:w=1.0:g={round(speech * 0.8, 2)}")
            filters.append(f"equalizer=f=4200:t=q:w=1.0:g={round(speech * 0.45, 2)}")

        # Yayın benzeri kompresör + limiter + gain
        filters.append("acompressor=threshold=-24dB:ratio=3.2:attack=6:release=180:makeup=2")
        filters.append("alimiter=limit=0.96")
        filters.append(f"volume={gain/100:.2f}")
        return ",".join(filters)

    def build_cmd(self, output_path, preview=False):
        inp = Path(self.input_path.get())
        out = Path(output_path)
        filt = self.build_filter()
        is_video = inp.suffix.lower() in VIDEO_EXTS
        cmd = ["ffmpeg", "-y"]
        if preview:
            cmd += ["-ss", "0", "-t", "15"]
        cmd += ["-i", str(inp)]
        if is_video and self.keep_video.get():
            cmd += ["-map", "0:v:0?", "-map", "0:a:0?", "-c:v", "copy", "-af", filt, "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
        else:
            cmd += ["-vn", "-af", filt, "-c:a", "pcm_s16le", str(out)]
        return cmd

    def validate(self):
        if not shutil.which("ffmpeg"):
            messagebox.showerror("FFmpeg yok", "FFmpeg bulunamadı. Kurulum: winget install Gyan.FFmpeg")
            return False
        if not self.input_path.get() or not Path(self.input_path.get()).exists():
            messagebox.showwarning("Dosya seç", "Önce giriş dosyasını seçin.")
            return False
        if not self.output_path.get():
            messagebox.showwarning("Çıkış seç", "Çıkış dosyası yolunu seçin.")
            return False
        return True

    def run_cmd(self, cmd, done_msg):
        self.progress.start(10)
        self.status.set("İşlem başladı. FFmpeg filtreleri uygulanıyor...")
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr[-2500:])
            self.status.set(done_msg)
            messagebox.showinfo("Tamamlandı", done_msg)
        except Exception as e:
            self.status.set("Hata oluştu.")
            messagebox.showerror("İşlem hatası", str(e))
        finally:
            self.progress.stop()

    def process_thread(self):
        if not self.validate():
            return
        cmd = self.build_cmd(self.output_path.get(), preview=False)
        threading.Thread(target=self.run_cmd, args=(cmd, "Temizleme tamamlandı: " + self.output_path.get()), daemon=True).start()

    def preview_thread(self):
        if not self.validate():
            return
        inp = Path(self.input_path.get())
        ext = ".mp4" if inp.suffix.lower() in VIDEO_EXTS and self.keep_video.get() else ".wav"
        preview_path = self.temp_dir / (inp.stem + "_onizleme" + ext)
        cmd = self.build_cmd(preview_path, preview=True)
        def worker():
            self.run_cmd(cmd, "15 saniyelik önizleme oluşturuldu: " + str(preview_path))
            if shutil.which("ffplay"):
                subprocess.Popen(["ffplay", "-autoexit", str(preview_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self._open_file(preview_path)
        threading.Thread(target=worker, daemon=True).start()

    def show_command(self):
        if not self.input_path.get():
            messagebox.showwarning("Dosya seç", "Önce giriş dosyasını seçin.")
            return
        cmd = self.build_cmd(self.output_path.get() or "output.mp4", preview=False)
        top = tk.Toplevel(self)
        top.title("FFmpeg Komutu")
        top.geometry("900x320")
        txt = tk.Text(top, wrap="word")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", " ".join('"'+c+'"' if ' ' in c else c for c in cmd))
        txt.configure(state="disabled")

    def open_output_folder(self):
        path = self.output_path.get()
        folder = Path(path).parent if path else Path.cwd()
        self._open_file(folder)

    def _open_file(self, path):
        path = str(path)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

if __name__ == "__main__":
    app = AudioCleanerApp()
    app.mainloop()
