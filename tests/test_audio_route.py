import unittest
from io import BytesIO
from app import app
import os
import threading

class AudioConversionTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('outputs', exist_ok=True)

        self.test_audio_path = 'tests/test.mp3'

    def tearDown(self):
        """Clean up after each test."""
        for folder in ['uploads', 'outputs']:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                os.remove(file_path)

    def test_convert_audio_required(self):
        """Test valid audio conversion with required parameters."""
        with open(self.test_audio_path, 'rb') as f:
            data = BytesIO(f.read())  # Read the real audio file
            data.seek(0)

            response = self.app.post('/audio/convert_audio',
                                    data={'file': (data, 'test.mp3'), 'output_format': 'wav'},
                                    content_type='multipart/form-data')

            self.assertEqual(response.status_code, 200)
            self.assertIn('File converted to wav successfully', response.json['message'])
            self.assertIn('output_file', response.json)
    
    def test_convert_audio_codec(self):
        """Test valid audio conversion with codec parameter."""
        with open(self.test_audio_path, 'rb') as f:
            data = BytesIO(f.read())
            data.seek(0)

            response = self.app.post('/audio/convert_audio',
                                    data={'file': (data, 'test.mp3'), 'output_format': 'wav', 'codec': 'pcm_s16le'},
                                    content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('File converted to wav successfully', response.json['message'])
            self.assertIn('output_file', response.json)

    def test_convert_audio_bitrate(self):
        """Test valid audio conversion with bitrate parameter."""
        with open(self.test_audio_path, 'rb') as f:
            data = BytesIO(f.read())
            data.seek(0)

            response = self.app.post('/audio/convert_audio',
                                    data={'file': (data, 'test.mp3'), 'output_format': 'wav', 'bitrate': '128k'},
                                    content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('File converted to wav successfully', response.json['message'])
            self.assertIn('output_file', response.json)
    
    def test_convert_audio_sample_rate(self):
        """Test valid audio conversion with sample rate parameter."""
        with open(self.test_audio_path, 'rb') as f:
            data = BytesIO(f.read())
            data.seek(0)

            response = self.app.post('/audio/convert_audio',
                                    data={'file': (data, 'test.mp3'), 'output_format': 'wav', 'sample_rate': '44100'},
                                    content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('File converted to wav successfully', response.json['message'])
            self.assertIn('output_file', response.json)
    
    def test_convert_audio_channels(self):
        """Test valid audio conversion with channels parameter."""
        with open(self.test_audio_path, 'rb') as f:
            data = BytesIO(f.read())
            data.seek(0)

            response = self.app.post('/audio/convert_audio',
                                    data={'file': (data, 'test.mp3'), 'output_format': 'wav', 'channels': '2'},
                                    content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('File converted to wav successfully', response.json['message'])
            self.assertIn('output_file', response.json)
    
    def test_convert_audio_volume(self):
        """Test valid audio conversion with volume parameter."""
        with open(self.test_audio_path, 'rb') as f:
            data = BytesIO(f.read())
            data.seek(0)

            response = self.app.post('/audio/convert_audio',
                                    data={'file': (data, 'test.mp3'), 'output_format': 'wav', 'volume': '4'},
                                    content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('File converted to wav successfully', response.json['message'])
            self.assertIn('output_file', response.json)
    
    def test_collision(self):
        """Test for filename collision."""
        def send_request():
            with open(self.test_audio_path, 'rb') as f:
                data = BytesIO(f.read())
                data.seek(0)

                response = self.app.post('/audio/convert_audio',
                                        data={'file': (data, 'test.mp3'), 'output_format': 'wav'},
                                        content_type='multipart/form-data')

                self.assertEqual(response.status_code, 200)
                self.assertIn('File converted to wav successfully', response.json['message'])
                self.assertIn('output_file', response.json)

            return response
        
        # Send two requests simultaneously
        threads = []
        for _ in range(2):
            thread = threading.Thread(target=send_request)
            threads.append(thread)
            thread.start()
        
        # exit
        for thread in threads:
            thread.join()

if __name__ == '__main__':
    unittest.main()
