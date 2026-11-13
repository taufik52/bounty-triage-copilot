# CIPOZ-STEPS.md — Langkah submit Arbiter Hacks V1 (Bounty Triage Copilot)

> **Status proyek: SIAP.** Unit test 13/13 dan E2E 9/9 sudah diverifikasi
> segar 12 Nov 2026 ~12:30 WIB. Yang tersisa HANYA langkah di bawah ini,
> semuanya butuh akun/login Cipoz sendiri (GitHub, YouTube, Devpost) —
> agen tidak bisa melakukannya.
>
> **Tenggat: 21 Desember 2026, 12:00 WIB** (20 Des 2026 21:00 PST /
> 21 Des 05:00 UTC). Penjurian 20–30 Des, pemenang diumumkan 31 Des 2026.
> Hadiah: $7.800 total, 5 hadiah uang tunai.
> Halaman hackathon: https://arbiter-hacks-v1.devpost.com
>
> **Peringatan eligibility (sudah diketahui Cipoz): students-only, usia
> 13+, tidak terbuka untuk perusahaan/organisasi profesional, dan tidak
> berlaku di Brazil, Crimea, Cuba, Iran, Korea Utara, Quebec, Rusia.**
> Pastikan kamu memenuhi syarat sebelum submit.

File proyek ada di `~/workspace/arbiter-hacks/`:
`app.py`, `triage.py`, `llm.py`, `samples.py`, `static/`, `README.md`,
`LICENSE` (MIT), `SUBMISSION.md` (draf isi form Devpost),
`DEMO-SCRIPT.md` (naskah video), `TEST-REPORT.md` (bukti test).

---

## Langkah 1 — Buat repo GitHub publik (di browser)

1. Buka https://github.com/new (login akun GitHub kamu).
2. Isi:
   - **Repository name:** `bounty-triage-copilot`
   - **Description:** `Score your bug-bounty draft against a triage rubric before a human triager does — instantly, privately, locally.`
   - **Public** (wajib — Devpost butuh repo publik).
   - **Jangan** centang "Add a README file", "Add .gitignore", atau
     "Choose a license" — semua file sudah ada di folder proyek.
3. Klik **Create repository**.
4. Catat URL repo-nya, contoh: `https://github.com/<username>/bounty-triage-copilot`

## Langkah 2 — Push kode dari VM ke repo itu

Jalankan di terminal VM (folder proyek):

```bash
cd ~/workspace/arbiter-hacks
git init
git add .
git commit -m "Bounty Triage Copilot — Arbiter Hacks V1 submission"
git branch -M main
git remote add origin https://github.com/<username>/bounty-triage-copilot.git
git push -u origin main
```

- Ganti `<username>` dengan username GitHub kamu.
- Saat diminta login, pakai **Personal Access Token (classic)** sebagai
  password, bukan password GitHub. Buat token di
  https://github.com/settings/tokens (centang scope `repo`).
  Token ini rahasia — jangan ditempel di chat atau file.
- Verifikasi: buka URL repo di browser — semua file (README, app.py,
  SUBMISSION.md, dst.) harus terlihat, dan README tampil di halaman repo.

## Langkah 3 — Rekam video demo 2–3 menit

Ikuti naskah lengkap di `DEMO-SCRIPT.md`. Ringkasnya:

1. Jalankan dulu di VM sebelum merekam:
   ```bash
   cd ~/workspace/arbiter-hacks
   python3 app.py            # http://127.0.0.1:8080
   ```
   Dan pastikan Ollama jalan supaya baris health menunjukkan OK:
   ```bash
   ollama serve
   ```
   (Kalau Ollama belum jalan, aplikasi tetap berfungsi — skor instan
   tidak butuh LLM. Tapi untuk video, health line "Ollama OK" lebih bagus.)
2. Rekam layar + voice-over Bahasa Inggris, total 2:00–3:00, 5 scene:
   - **Scene 1 (0:00–0:25):** masalah — triage rejection yang bisa dicegah.
   - **Scene 2 (0:25–1:15):** klik contoh **weak draft** → Score →
     tunjukkan **7/100, Grade F, "Not submittable yet"** + 2 saran.
   - **Scene 3 (1:15–1:55):** klik contoh **strong draft** → Score →
     tunjukkan **93/100, Grade A, "Submission-ready"** + severity match.
   - **Scene 4 (1:55–2:25):** klik **"Ask local LLM"**, jelaskan data
     tidak keluar dari mesin. **Jangan tunggu balasan penuh LLM di
     kamera** — di CPU VM ini satu review penuh butuh 10+ menit.
     Bilang saja: review LLM itu opsional di latar, skor instan tidak
     pernah menunggu.
   - **Scene 5 (2:25–2:35):** penutup + tampilkan URL repo dan
     `python3 app.py`.
3. Upload ke YouTube sebagai **Public** atau **Unlisted** (Devpost butuh
   link yang bisa dibuka juri). Catat URL videonya.

## Langkah 4 — Submit di Devpost

1. Buka https://arbiter-hacks-v1.devpost.com dan login akun Devpost kamu.
2. Klik **Register** / **Join the hackathon** (kalau belum terdaftar),
   lalu **Submit a project** / **Enter a submission**.
3. Isi form dengan isi `SUBMISSION.md` (sudah ditulis dalam Bahasa
   Inggris, tinggal salin-tempel):
   - **Title:** `Bounty Triage Copilot`
   - **Tagline:** `Score your bug-bounty draft against a triage rubric before a human triager does — instantly, privately, locally.`
   - **Description:** salin bagian Description + What we built +
     What we learned + What's next dari `SUBMISSION.md`.
   - **Track:** General Track.
   - **Built with:** `Python (standard library only), HTML/CSS/JavaScript, Ollama (qwen2.5:3b, local)`
   - **Code repository:** URL repo GitHub dari Langkah 2.
   - **Demo video:** URL YouTube dari Langkah 3.
   - **How to run:** `python3 app.py` → http://127.0.0.1:8080
     (opsional LLM: `ollama pull qwen2.5:3b && ollama serve`).
4. Simpan sebagai **Draft** dulu, periksa semua link bisa dibuka
   (buka repo + video dari mode incognito), baru klik **Submit**.

## Langkah 5 — Ceklis akhir sebelum tenggat

- [ ] Repo GitHub publik, semua file ter-push, README tampil.
- [ ] Video YouTube 2–3 menit, Public/Unlisted, skor 7/100 dan 93/100
      terlihat jelas.
- [ ] Form Devpost terisi lengkap (judul, tagline, deskripsi, repo,
      video, Built with, track).
- [ ] Semua link di form Devpost bisa dibuka tanpa login.
- [ ] Submission Devpost berstatus **Submitted** (bukan Draft) sebelum
      **21 Des 2026, 12:00 WIB**.

## Kalau ada yang gagal

- **Push ditolak / auth gagal:** token GitHub salah atau kedaluwarsa —
  buat token baru di https://github.com/settings/tokens (scope `repo`).
- **App tidak jalan saat rekam:** `python3 app.py` butuh Python 3.10+,
  tanpa dependensi. Cek `TEST-REPORT.md` untuk perintah test ulang:
  `python3 -m unittest test_triage test_llm_parse -v` dan
  `bash test_e2e.sh`.
- **LLM lambat/tidak merespons saat demo:** itu normal di VM ini
  (~7 detik/token). Klik LLM paling akhir dan jangan tunggu balasannya —
  naskah demo sudah menuliskan ini. Skor instan 93/100 dan 7/100 tidak
  terpengaruh sama sekali.

## Bukti kesiapan (12 Nov 2026 ~12:30 WIB)

- Unit test: **13/13 lolos** (`python3 -m unittest test_triage test_llm_parse -v`)
- E2E: **9/9 lolos** (`bash test_e2e.sh`), latensi skor 0,0019 dtk
- Draf kuat: **93/100 Grade A**, draf lemah: **7/100 Grade F**
- Server live: `/api/health` → `ollama_available: true`, model
  `qwen2.5:3b` tersedia
- Fallback LLM terverifikasi: `LLM_TIMEOUT=30` → HTTP 502 setelah
  30,1 dtk dengan pesan graceful, skor rules-based tetap berdiri
- Detail lengkap: `TEST-REPORT.md`
