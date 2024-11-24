# .mp3 -> .wav

```bash
curl -X POST -F "file=@/path/to/example.mp3" http://127.0.0.1:5000/mp3_to_wav
```

# .wav -> .mp3

```bash
curl -X POST -F "file=@/path/to/example.wav" http://127.0.0.1:5000/wav_to_mp3
```

# Download

```bash
curl -O http://127.0.0.1:5000/download/example.wav
```