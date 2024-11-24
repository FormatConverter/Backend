# Convert

```bash
curl -X POST -F "file=@yourfile.wav" -F "output_format=mp3" -F "codec=pcm_s16le" -F "bitrate=192k" -F "sample_rate=44100" -F "channels=2" http://localhost:5000/convert
```

# Download

```bash
curl -O http://127.0.0.1:5000/download/example.wav
```