import azure.cognitiveservices.speech as speechsdk
import os
import hashlib
from typing import Optional


class TTSService:
    def __init__(self, config):
        self.config = config
        self.speech_key = config['azure_tts'].get('subscription_key')
        self.region = config['azure_tts'].get('region')
        self.voice_name = config['azure_tts'].get('voice_name', 'en-US-JennyNeural')
        self.language = config['azure_tts'].get('language', 'en-US')
        
        if not self.speech_key or not self.region:
            print("Warning: Azure TTS credentials not configured")
    
    def generate_audio(self, text: str, session_dir: str) -> Optional[str]:
        """
        Generate audio file from text using Azure TTS
        
        Args:
            text: Text to convert to speech
            session_dir: Directory to save audio file
            
        Returns:
            Path to generated audio file, or None if failed
        """
        try:
            if not self.speech_key or not self.region:
                print("Azure TTS not configured, using fallback")
                return self._generate_fallback_audio(text, session_dir)
            
            # Check cache first
            text_hash = hashlib.md5(text.encode()).hexdigest()
            audio_filename = f"audio_{text_hash}.wav"
            audio_path = os.path.join(session_dir, audio_filename)
            
            if os.path.exists(audio_path):
                print(f"Using cached audio for: {text}")
                return audio_path
            
            # Configure Azure Speech SDK
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.region
            )
            speech_config.speech_synthesis_voice_name = self.voice_name
            speech_config.speech_synthesis_language = self.language
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=None
            )
            
            # Generate SSML for better control
            ssml = self._create_ssml(text)
            
            # Synthesize speech
            print(f"Generating audio for: {text}")
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Save audio data to file
                with open(audio_path, 'wb') as audio_file:
                    audio_file.write(result.audio_data)
                
                print(f"Audio generated successfully: {audio_filename}")
                return audio_path
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation_details.error_details}")
                
                # Try fallback
                return self._generate_fallback_audio(text, session_dir)
            
        except Exception as e:
            print(f"Error generating audio with Azure TTS: {e}")
            return self._generate_fallback_audio(text, session_dir)
        
        return None
    
    def _create_ssml(self, text: str) -> str:
        """Create SSML markup for better speech synthesis"""
        ssml = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{self.language}">
            <voice name="{self.voice_name}">
                <prosody rate="0.9" pitch="medium">
                    {text}
                </prosody>
                <break time="500ms"/>
            </voice>
        </speak>
        '''
        return ssml.strip()
    
    def _generate_fallback_audio(self, text: str, session_dir: str) -> Optional[str]:
        """
        Fallback audio generation using system TTS or pre-recorded audio
        This is a placeholder - you might want to implement:
        1. System TTS (macOS 'say' command, Windows SAPI, etc.)
        2. Alternative TTS services
        3. Pre-recorded audio files
        """
        try:
            text_hash = hashlib.md5(text.encode()).hexdigest()
            audio_filename = f"fallback_audio_{text_hash}.wav"
            audio_path = os.path.join(session_dir, audio_filename)
            
            if os.path.exists(audio_path):
                return audio_path
            
            # Try system TTS (macOS example)
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':  # macOS
                # Use macOS 'say' command
                temp_aiff = audio_path.replace('.wav', '.aiff')
                cmd = ['say', '-o', temp_aiff, text]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Convert AIFF to WAV using ffmpeg
                    convert_cmd = ['ffmpeg', '-i', temp_aiff, '-y', audio_path]
                    convert_result = subprocess.run(convert_cmd, capture_output=True)
                    
                    if convert_result.returncode == 0:
                        # Clean up temp file
                        if os.path.exists(temp_aiff):
                            os.remove(temp_aiff)
                        
                        print(f"Generated fallback audio using system TTS: {audio_filename}")
                        return audio_path
            
            elif platform.system() == 'Windows':
                # Windows SAPI example (requires additional setup)
                pass
            
            elif platform.system() == 'Linux':
                # Linux espeak example
                cmd = ['espeak', '-w', audio_path, text]
                result = subprocess.run(cmd, capture_output=True)
                
                if result.returncode == 0 and os.path.exists(audio_path):
                    print(f"Generated fallback audio using espeak: {audio_filename}")
                    return audio_path
            
            # If all else fails, create a silent audio file as placeholder
            return self._create_silent_audio(text, audio_path)
            
        except Exception as e:
            print(f"Error generating fallback audio: {e}")
            return self._create_silent_audio(text, session_dir)
    
    def _create_silent_audio(self, text: str, session_dir: str) -> str:
        """Create a silent audio file as ultimate fallback"""
        try:
            from pydub import AudioSegment
            
            # Create 2 seconds of silence
            duration_ms = 2000
            silent_audio = AudioSegment.silent(duration=duration_ms)
            
            text_hash = hashlib.md5(text.encode()).hexdigest()
            audio_filename = f"silent_audio_{text_hash}.wav"
            audio_path = os.path.join(session_dir, audio_filename)
            
            silent_audio.export(audio_path, format="wav")
            
            print(f"Created silent audio placeholder: {audio_filename}")
            print(f"Note: Add text '{text}' to subtitle track")
            
            return audio_path
            
        except Exception as e:
            print(f"Error creating silent audio: {e}")
            return None
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_wav(audio_path)
            duration_seconds = len(audio) / 1000.0
            
            return duration_seconds
            
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 2.0  # Default duration
