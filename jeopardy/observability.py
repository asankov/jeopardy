"""
Phoenix observability configuration for LLM tracing.

This module sets up Arize Phoenix for observing OpenAI API calls.
"""
import logging
import os

from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

logger = logging.getLogger(__name__)


def setup_phoenix_tracing(project_name: str = "jeopardy-api"):
    """
    Set up Phoenix tracing for OpenAI instrumentation.

    Environment Variables:
        PHOENIX_ENDPOINT: Phoenix server endpoint (default: http://127.0.0.1:6006/v1/traces)
        PHOENIX_ENABLED: Set to "false" to disable Phoenix tracing (default: "true")
    """
    # Check if Phoenix is enabled
    phoenix_enabled = os.getenv("PHOENIX_ENABLED", "true").lower() == "true"
    if not phoenix_enabled:
        logger.info("Phoenix tracing is disabled")
        return

    # Get Phoenix endpoint from environment or use default
    endpoint = os.getenv("PHOENIX_ENDPOINT", "http://127.0.0.1:6006/v1/traces")

    logger.info(f"Setting up Phoenix tracing at {endpoint}")

    # Create tracer provider
    tracer_provider = trace_sdk.TracerProvider(
        resource=trace_sdk.Resource.create({"service.name": project_name})
    )

    # Add OTLP span processor for Phoenix
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        tracer_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))
        logger.info("Phoenix OTLP exporter configured successfully")
    except Exception as e:
        logger.warning(f"Failed to configure Phoenix: {e}")
        return

    # Instrument OpenAI
    try:
        OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("OpenAI instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument OpenAI: {e}")
