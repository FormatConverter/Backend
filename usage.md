# Convert

## Audio
```bash
curl -X POST -F "file=@yourfile.wav" -F "output_format=mp3" -F "codec=pcm_s16le" -F "bitrate=192k" -F "sample_rate=44100" -F "channels=2" -F "volume=1.5" http://localhost:5000/convert_audio
```

## Image
```bash
curl -X POST -F "file=@yourfile.jpg" -F "output_format=png" -F "width=500" -F "height=800" -F "quality=2" http://localhost:5000/convert_image
```


# Download

```bash
curl -O http://127.0.0.1:5000/download/example.wav
```