import logging
import concurrent.futures
import os
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class WhisperService:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Initializes the Whisper model.
        
        Args:
            model_size: Size of the model (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Quantization type (int8, float16, etc.)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # Load model immediately to fail fast if there are issues
        self.load_model()

    def load_model(self):
        try:
            logger.info(f"Loading Whisper model: {self.model_size} on {self.device}...")
            # download_root can be specified if needed, but we rely on environment/defaults
            # which we mapped to /root/.cache/huggingface in docker-compose
            self.model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type,
                # Enable Flash Attention 2 if on CUDA (requires matching compute capability, usually safe on 4060)
                flash_attention=True if self.device == "cuda" else False,
                cpu_threads=4
            )
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise e
        
        # Initialize Batched Pipeline for GPU
        if self.device == "cuda":
            try:
                from faster_whisper import BatchedInferencePipeline
                self.batched_model = BatchedInferencePipeline(model=self.model)
                logger.info("BatchedInferencePipeline initialized for GPU acceleration.")
            except ImportError:
                logger.warning("BatchedInferencePipeline not available. Using standard inference.")
                self.batched_model = None
            except Exception as e:
                logger.warning(f"Failed to initialize BatchedInferencePipeline: {e}")
                self.batched_model = None

    def transcribe(self, audio_file_path: str) -> dict:
        """
        Transcribes the given audio file efficiently.
        
        Args:
            audio_file_path: Path to the audio file.
            
        Returns:
            dict: {
                "text": str,
                "language": str,
                "duration": float
            }
        """
        if not self.model:
            raise RuntimeError("Model not loaded")

        if not os.path.exists(audio_file_path):
             raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        try:
            # transcription is CPU/GPU intensive and blocking, so we run it in a thread
            
            # Use BatchedInferencePipeline if enabled and on GPU
            transcribe_func = self.model.transcribe
            
            # Check if we should use batching
            # For simplicity, we assume if we are on CUDA we want batching if available
            # We need to use internal method or wrapper
            # Actually, standard model.transcribe does NOT use batching.
            # We need to initialize BatchedInferencePipeline.
            # See initialization below.
            
            if hasattr(self, 'batched_model') and self.batched_model:
                 segments, info = self.batched_model.transcribe(audio_file_path, batch_size=16)
            else:
                 segments, info = self.model.transcribe(audio_file_path, beam_size=5)
            
            # segments is a generator, so we must iterate to get the text
            # This is where the actual processing happens
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)

            full_text = "".join(text_segments).strip()
            
            return {
                "text": full_text,
                "language": info.language,
                "duration": info.duration
            }
        except Exception as e:
            logger.error(f"Error during transcription of {audio_file_path}: {e}")
            raise e

    async def transcribe_async(self, audio_file_path: str):
        """
        Async wrapper for transcribe method to use with FastAPI
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self.transcribe, audio_file_path)
