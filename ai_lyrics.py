import os
import threading
import customtkinter as ctk

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_SIZE = "base"

def is_model_installed():
    # Назви папок, які створює faster-whisper при завантаженні (залежить від версії huggingface_hub)
    model_path = os.path.join(MODELS_DIR, f"models--Systran--faster-whisper-{MODEL_SIZE}")
    # Інший можливий шлях (якщо download_model кидає прямо в папку)
    direct_path = os.path.join(MODELS_DIR, f"faster-whisper-{MODEL_SIZE}")
    
    if os.path.exists(model_path) and len(os.listdir(model_path)) > 2:
        return True
    if os.path.exists(direct_path) and len(os.listdir(direct_path)) > 2:
        return True
    # Якщо він збережений прямо в MODELS_DIR (model.bin)
    if os.path.exists(os.path.join(MODELS_DIR, "model.bin")):
        return True
        
    return False

def download_ai_model_ui(app, on_complete=None):
    dialog = ctk.CTkToplevel(app)
    dialog.title("Завантаження AI Моделі")
    dialog.geometry("450x200")
    dialog.attributes('-topmost', True)
    dialog.grab_set()
    dialog.resizable(False, False)

    dialog.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() - 450) // 2
    y = app.winfo_y() + (app.winfo_height() - 200) // 2
    dialog.geometry(f"+{x}+{y}")

    lbl_title = ctk.CTkLabel(dialog, text="Встановлення AI моделі (Whisper)", font=ctk.CTkFont(size=16, weight="bold"))
    lbl_title.pack(pady=(20, 10))

    lbl_info = ctk.CTkLabel(dialog, text="Завантажуємо ~250 МБ даних. Це потрібно зробити\nлише один раз. Будь ласка, зачекайте...", font=ctk.CTkFont(size=13), text_color="gray")
    lbl_info.pack(pady=(0, 15))

    progressbar = ctk.CTkProgressBar(dialog, width=350, mode="indeterminate", progress_color="#E52D27")
    progressbar.pack(pady=10)
    progressbar.start()

    def _download_task():
        try:
            from faster_whisper import download_model
            # Завантажуємо модель
            model_path = download_model(MODEL_SIZE, output_dir=os.path.join(MODELS_DIR, f"faster-whisper-{MODEL_SIZE}"))
            
            # Після успіху
            app.after(0, progressbar.stop)
            app.after(0, lambda: lbl_info.configure(text="✅ Модель успішно встановлена!", text_color="#10b981"))
            app.after(2000, dialog.destroy)
            if on_complete:
                app.after(2000, on_complete)
        except Exception as e:
            app.after(0, progressbar.stop)
            app.after(0, lambda: lbl_info.configure(text=f"❌ Помилка: {e}", text_color="#ef4444"))
            app.after(3000, dialog.destroy)

    threading.Thread(target=_download_task, daemon=True).start()

def transcribe_audio_ui(app, audio_path, on_success=None):
    dialog = ctk.CTkToplevel(app)
    dialog.title("ШІ слухає пісню...")
    dialog.geometry("400x200")
    dialog.attributes('-topmost', True)
    dialog.grab_set()
    dialog.resizable(False, False)

    dialog.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() - 400) // 2
    y = app.winfo_y() + (app.winfo_height() - 200) // 2
    dialog.geometry(f"+{x}+{y}")

    lbl = ctk.CTkLabel(dialog, text="🎵 ШІ генерує текст пісні...", font=ctk.CTkFont(size=15, weight="bold"))
    lbl.pack(pady=(20, 10))

    progressbar = ctk.CTkProgressBar(dialog, width=300, progress_color="#E52D27")
    progressbar.set(0)
    progressbar.pack(pady=10)
    
    status_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    status_frame.pack(fill="x", padx=50)
    
    lbl_percent = ctk.CTkLabel(status_frame, text="0%", font=ctk.CTkFont(weight="bold"))
    lbl_percent.pack(side="left")
    
    lbl_eta = ctk.CTkLabel(status_frame, text="Оцінка часу...", text_color="gray")
    lbl_eta.pack(side="right")
    
    def update_ui(p, pct_text, eta_text):
        progressbar.set(p)
        lbl_percent.configure(text=pct_text)
        lbl_eta.configure(text=eta_text)

    def _transcribe_task():
        import time
        try:
            from faster_whisper import WhisperModel
            model_path = os.path.join(MODELS_DIR, f"faster-whisper-{MODEL_SIZE}")
            model = WhisperModel(model_path, device="cpu", compute_type="int8")
            
            # Транскрибуємо з увімкненими мітками на рівні слів
            segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
            total_duration = info.duration
            
            text_lines = []
            start_time = time.time()
            
            for segment in segments:
                current_chunk = []
                chunk_start = None
                
                if segment.words:
                    for word_obj in segment.words:
                        if chunk_start is None:
                            chunk_start = word_obj.start
                            
                        word_text = word_obj.word.strip()
                        if word_text:
                            current_chunk.append(word_text)
                            
                        # Розбиваємо, якщо зібрали 5 слів або є розділовий знак
                        if len(current_chunk) >= 5 or any(p in word_text for p in '.?!,'):
                            m = int(chunk_start // 60)
                            s = chunk_start % 60
                            text_lines.append(f"[{m:02d}:{s:05.2f}] {' '.join(current_chunk)}")
                            current_chunk = []
                            chunk_start = None
                            
                    # Додаємо залишок
                    if current_chunk:
                        m = int(chunk_start // 60)
                        s = chunk_start % 60
                        text_lines.append(f"[{m:02d}:{s:05.2f}] {' '.join(current_chunk)}")
                else:
                    # Фоллбек, якщо слів немає (але є сегмент)
                    m = int(segment.start // 60)
                    s = segment.start % 60
                    text_lines.append(f"[{m:02d}:{s:05.2f}] {segment.text.strip()}")
                
                # Розрахунок прогресу
                percent = min(segment.end / total_duration, 1.0) if total_duration > 0 else 0
                elapsed = time.time() - start_time
                if percent > 0:
                    total_estimated = elapsed / percent
                    eta = total_estimated - elapsed
                    eta_m = int(eta // 60)
                    eta_s = int(eta % 60)
                    eta_str = f"Залишилось: {eta_m}:{eta_s:02d}"
                else:
                    eta_str = "Оцінка часу..."
                    
                app.after(0, update_ui, percent, f"{int(percent*100)}%", eta_str)
            
            full_text = "\n".join(text_lines)
            
            # Зберігаємо у файл
            try:
                from mutagen.id3 import ID3, USLT, ID3NoHeaderError
                try:
                    tags = ID3(audio_path)
                except ID3NoHeaderError:
                    tags = ID3()
                
                tags.delall('USLT')
                tags.add(USLT(encoding=3, lang='eng', desc='desc', text=full_text))
                tags.save(audio_path, v2_version=3)
            except Exception as e:
                print(f"Failed to save lyrics to ID3: {e}")

            app.after(0, dialog.destroy)
            
            if on_success:
                app.after(0, lambda: on_success(full_text))
                
        except Exception as e:
            app.after(0, lambda: lbl.configure(text=f"❌ Помилка: {e}", text_color="#ef4444"))
            app.after(3000, dialog.destroy)

    threading.Thread(target=_transcribe_task, daemon=True).start()
