import sys
import os
import re
from datetime import datetime
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog

class AMVMaker:
    def __init__(self, root):
        self.root = root
        self.root.title('AMV-Maker')
        self.root.geometry('450x250')

        main_layout = ttk.Frame(root, padding=10)
        main_layout.pack(fill=tk.BOTH, expand=True)

        v_lay = ttk.Frame(main_layout)
        v_lay.pack(fill=tk.X, pady=2)
        self.v_in = ttk.Entry(v_lay)
        self.v_in.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        btn_v = ttk.Button(v_lay, text='Video', command=lambda: self.v_in.delete(0, tk.END) or self.v_in.insert(0, filedialog.askopenfilename(title='Video', filetypes=[('Video Files', '*.mp4')])))
        btn_v.pack(side=tk.RIGHT)

        a_lay = ttk.Frame(main_layout)
        a_lay.pack(fill=tk.X, pady=2)
        self.a_in = ttk.Entry(a_lay)
        self.a_in.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        btn_a = ttk.Button(a_lay, text='Audio', command=lambda: self.a_in.delete(0, tk.END) or self.a_in.insert(0, filedialog.askopenfilename(title='Audio', filetypes=[('Audio Files', '*.mp3')])))
        btn_a.pack(side=tk.RIGHT)

        s_lay = ttk.Frame(main_layout)
        s_lay.pack(fill=tk.X, pady=2)
        self.s_in = ttk.Entry(s_lay)
        self.s_in.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        btn_s = ttk.Button(s_lay, text='Save To', command=lambda: self.s_in.delete(0, tk.END) or self.s_in.insert(0, filedialog.askdirectory(title='Select Directory')))
        btn_s.pack(side=tk.RIGHT)

        q_lay = ttk.Frame(main_layout)
        q_lay.pack(fill=tk.X, pady=5)
        ttk.Label(q_lay, text='Quality:').pack(side=tk.LEFT, padx=(0, 5))
        self.q_combo = ttk.Combobox(q_lay, state="readonly")
        self.q_combo['values'] = ['144p (256x144)', '240p (426x240)', '360p (640x360)', '480p (854x480)', '720p (1280x720)', '1080p (1920x1080)']
        self.q_combo.current(0)
        self.q_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.p_bar = ttk.Progressbar(main_layout, orient='horizontal', mode='determinate', maximum=100)
        self.p_bar.pack(fill=tk.X, pady=5)

        self.status = ttk.Label(main_layout, text='Status: Idle')
        self.status.pack(anchor=tk.W, pady=2)

        self.btn_make = ttk.Button(main_layout, text='make amv', command=self.convert)
        self.btn_make.pack(fill=tk.X, pady=(5, 0))
        
        self.total_duration = 0.0

    def get_dur(self, path):
        try:
            output = subprocess.check_output(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path],
                stderr=subprocess.DEVNULL
            ).decode().strip().replace(',', '.')
            return float(output)
        except Exception:
            return 0.0

    def convert(self):
        v, a, s = self.v_in.get(), self.a_in.get(), self.s_in.get()
        if not v or not a: return

        self.btn_make.config(state=tk.DISABLED)
        self.status.config(text='Analyzing durations...')
        self.p_bar['value'] = 0
        
        self.total_duration = self.get_dur(a)
        dur_v = self.get_dur(v)

        if self.total_duration == 0.0 or dur_v == 0.0:
            self.status.config(text='Error: ffprobe failed!')
            self.btn_make.config(state=tk.NORMAL)
            return

        self.status.config(text='Encoding...')
        speed = str(round(self.total_duration / dur_v, 5)).replace(',', '.')
        filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        out = os.path.join(s, filename) if s else filename

        quality_profiles = {
            0: {'scale': '256:144',   'profile': 'main', 'level': '1.1', 'b_v': '100k',  'maxr': '150k',  'buf': '300k',  'r': '15', 'b_a': '64k'},
            1: {'scale': '426:240',   'profile': 'main', 'level': '1.2', 'b_v': '250k',  'maxr': '350k',  'buf': '600k',  'r': '24', 'b_a': '96k'},
            2: {'scale': '640:360',   'profile': 'main', 'level': '2.1', 'b_v': '500k',  'maxr': '700k',  'buf': '1200k', 'r': '24', 'b_a': '96k'},
            3: {'scale': '854:480',   'profile': 'main', 'level': '3.0', 'b_v': '1000k', 'maxr': '1500k', 'buf': '2000k', 'r': '30', 'b_a': '128k'},
            4: {'scale': '1280:720',  'profile': 'high', 'level': '3.1', 'b_v': '2500k', 'maxr': '3500k', 'buf': '5000k', 'r': '30', 'b_a': '168k'},
            5: {'scale': '1920:1080', 'profile': 'high', 'level': '4.0', 'b_v': '4500k', 'maxr': '6000k', 'buf': '9000k', 'r': '30', 'b_a': '192k'}
        }
        
        p = quality_profiles[self.q_combo.currentidx if hasattr(self.q_combo, 'currentidx') else self.q_combo.current()]

        args = ['ffmpeg', '-y', '-progress', 'pipe:1', '-i', v, '-i', a, '-vf', f"setpts={speed}*PTS,scale={p['scale']}", 
                '-c:v', 'libx264', '-profile:v', p['profile'], '-level', p['level'], '-b:v', p['b_v'], 
                '-maxrate', p['maxr'], '-bufsize', p['buf'], '-r', p['r'], '-c:a', 'aac', '-b:a', p['b_a'], 
                '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-movflags', '+faststart', out]

        threading.Thread(target=self._run_ffmpeg, args=(args, filename), daemon=True).start()

    def _run_ffmpeg(self, args, filename):
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
        
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                self.parse_progress(line)
        
        self.root.after(0, lambda: [
            self.status.config(text=f'Done: {filename}'), 
            self.p_bar.configure(value=100), 
            self.btn_make.config(state=tk.NORMAL)
        ])

    def parse_progress(self, output):
        match = re.search(r'out_time_us=(\d+)', output)
        if match and self.total_duration > 0:
            current_time = float(match.group(1)) / 1000000.0
            percent = int((current_time / self.total_duration) * 100)
            self.root.after(0, lambda p=percent: self.p_bar.configure(value=min(p, 99)))

if __name__ == '__main__':
    root = tk.Tk()
    app = AMVMaker(root)
    root.mainloop()
