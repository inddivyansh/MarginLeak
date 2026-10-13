import os
import json
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.ai.prompt_templates import SYSTEM_PROMPT, INFERENCE_PROMPT_TEMPLATE
from backend.app.ai.fallback_engine import FallbackNormalizer

logger = logging.getLogger(__name__)

class TinkerModelClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.tinker_api_key
        self.client = None
        self.sampling_client = None
        self.model_name = os.getenv("TINKER_MODEL_NAME", "Qwen/Qwen3-8B")
        self.model_path = settings.tinker_model_path or os.getenv("TINKER_MODEL_PATH")
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.info("Tinker API key not configured. Using deterministic fallback engine.")
            return

        try:
            import tinker
            self.client = tinker.ServiceClient(api_key=self.api_key)
            # Create sampling client for inference
            try:
                if self.model_path:
                    self.sampling_client = self.client.create_sampling_client(model_path=self.model_path)
                    logger.info("Initialized Tinker sampling client from configured model path")
                else:
                    self.sampling_client = self.client.create_sampling_client(base_model=self.model_name)
                    logger.info(f"Initialized Tinker base-model sampling client with model {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to create Tinker sampling client: {e}. Will use fallback.")
        except ImportError:
            logger.warning("tinker package not installed. Using fallback.")
        except Exception as e:
            logger.warning(f"Error initializing Tinker ServiceClient: {e}")

    def normalize_line(self, description: str, sku: Optional[str] = None) -> Dict[str, Any]:
        """
        Normalizes a supplier line item description using the Tinker fine-tuned model
        or gracefully falls back to the deterministic engine.
        """
        if not self.sampling_client:
            return FallbackNormalizer.normalize(description, sku)

        try:
            prompt = f"{SYSTEM_PROMPT}\n\n{INFERENCE_PROMPT_TEMPLATE.format(supplier_description=description, supplier_sku=sku or 'None')}"
            import tinker
            tokenizer = self.sampling_client.get_tokenizer()
            response = self.sampling_client.sample(
                tinker.types.ModelInput.from_ints(tokenizer.encode(prompt)),
                1,
                tinker.types.SamplingParams(max_tokens=256, temperature=0.0),
            ).result()

            # Parse JSON from model output
            text = tokenizer.decode(response.sequences[0].tokens).strip()
            # Find JSON block
            if "{" in text and "}" in text:
                json_str = text[text.find("{"):text.rfind("}") + 1]
                data = json.loads(json_str)
                return {
                    "canonical_description": data.get("canonical_description", description),
                    "pack_quantity": int(data.get("pack_quantity", 1)),
                    "pack_unit": str(data.get("pack_unit", "each")),
                    "size": data.get("size"),
                    "attributes": data.get("attributes", []),
                    "uncertain_fields": data.get("uncertain_fields", [])
                }
            else:
                return FallbackNormalizer.normalize(description, sku)
        except Exception as e:
            logger.warning(f"Tinker inference failed ({e}). Falling back to deterministic engine.")
            return FallbackNormalizer.normalize(description, sku)

tinker_client = TinkerModelClient()
