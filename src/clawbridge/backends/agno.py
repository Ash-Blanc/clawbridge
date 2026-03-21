"""
Agno backend — compiles ClawAgent into Agno's Agent primitive.

Agno uses a declarative Agent class with modular tools, memory,
knowledge, and team composition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clawbridge.backends.base import ClawBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.session import OpenClawSessionContext
from clawbridge.core.types import LLMProvider


class AgnoBackend(ClawBackend):
    """Compile and run OpenClaw-style agent specs using Agno."""

    name = "agno"

    def __init__(self, agent: ClawAgent, memory: ClawMemory | None = None):
        super().__init__(agent, memory)
        # Lazy imports to avoid hard dependency
        self._agno_mod: Any = None

    def _ensure_imports(self) -> None:
        """Lazy-import Agno modules."""
        if self._agno_mod is not None:
            return
        try:
            import agno.agent
            import agno.models
            import agno.tools
            from agno.os import AgentOS
            self._agno_mod = {
                "Agent": agno.agent.Agent,
                "models": agno.models,
                "tools": agno.tools,
                "AgentOS": AgentOS,
            }
        except ImportError:
            raise ImportError(
                "Agno is not installed. Run: pip install clawbridge[agno]"
            )

    def _resolve_model(self) -> Any:
        """Map a ClawAgent model config to an Agno model instance."""
        self._ensure_imports()
        cfg = self.agent.model

        model_map: dict[LLMProvider, tuple[str, str]] = {
            LLMProvider.OPENAI: ("agno.models.openai", "OpenAIChat"),
            LLMProvider.ANTHROPIC: ("agno.models.anthropic", "Claude"),
            LLMProvider.GROQ: ("agno.models.groq", "Groq"),
            LLMProvider.DEEPSEEK: ("agno.models.deepseek", "DeepSeek"),
            LLMProvider.LOCAL: ("agno.models.openai", "OpenAILike"),
        }

        if cfg.provider not in model_map:
            raise ValueError(f"Unsupported Agno model provider: {cfg.provider}")

        module_path, class_name = model_map[cfg.provider]
        import importlib
        mod = importlib.import_module(module_path)
        model_cls = getattr(mod, class_name)

        kwargs: dict[str, Any] = {"id": cfg.model_id}
        model_fields = getattr(model_cls, "__dataclass_fields__", {})

        if "temperature" in model_fields:
            kwargs["temperature"] = cfg.temperature
        if "max_tokens" in model_fields:
            kwargs["max_tokens"] = cfg.max_tokens
        elif "max_output_tokens" in model_fields:
            kwargs["max_output_tokens"] = cfg.max_tokens
        if cfg.api_key:
            kwargs["api_key"] = cfg.api_key
        if cfg.base_url:
            kwargs["base_url"] = cfg.base_url

        return model_cls(**kwargs)

    def _build_tools(self) -> list[Any]:
        """
        Convert ClawAgent tools into Agno tool callables.
        """
        agno_tools: list[Any] = []
        missing_implementations: list[str] = []

        for tool_def in self.agent.get_all_tools():
            if tool_def.callable is not None:
                agno_tools.append(tool_def.callable)
            else:
                missing_implementations.append(tool_def.name)

        if missing_implementations:
            missing = ", ".join(sorted(missing_implementations))
            raise ValueError(
                "Agno tools require real Python callables. "
                f"Missing implementations for: {missing}"
            )

        return agno_tools

    def _build_memory(self) -> Any | None:
        """Build Agno-native memory (Db) from ClawAgent storage config."""
        if not self.agent.storage.enabled:
            return None
            
        try:
            storage = self.agent.storage
            if storage.type == "in_memory":
                from agno.db.in_memory import InMemoryDb
                return InMemoryDb()
            elif storage.type == "sqlite":
                from agno.db.sqlite import SqliteDb
                return SqliteDb(db_file=storage.db_url)
            elif storage.type == "postgres":
                from agno.db.postgres import PostgresDb
                return PostgresDb(db_url=storage.db_url)
        except ImportError as exc:
            raise ImportError(
                "Agno storage requires optional database dependencies. "
                "Install clawbridge[agno] with SQL backends enabled."
            ) from exc
        return None

    def _build_embedder(self) -> Any:
        from agno.knowledge.embedder.openai import OpenAIEmbedder

        kwargs: dict[str, Any] = {}
        if self.agent.knowledge.embedder_model_id:
            kwargs["id"] = self.agent.knowledge.embedder_model_id
        return OpenAIEmbedder(**kwargs)

    def _build_knowledge(self) -> Any | None:
        """Build Agno Knowledge base from ClawAgent knowledge config."""
        if not self.agent.knowledge.enabled:
            return None
            
        try:
            from agno.knowledge.knowledge import Knowledge
            
            k_config = self.agent.knowledge
            vector_db: Any = None
            embedder = self._build_embedder()
            
            if k_config.type == "lancedb":
                from agno.vectordb.lancedb import LanceDb, SearchType
                vector_db = LanceDb(
                    uri=k_config.db_url,
                    table_name=k_config.table_name,
                    search_type=SearchType.hybrid,
                    embedder=embedder,
                    use_tantivy=False,
                )
            elif k_config.type == "pgvector":
                from agno.vectordb.pgvector import PgVector, SearchType
                vector_db = PgVector(
                    db_url=k_config.db_url,
                    table_name=k_config.table_name,
                    search_type=SearchType.hybrid,
                    embedder=embedder,
                )
                
            if vector_db:
                knowledge = Knowledge(
                    vector_db=vector_db,
                    max_results=k_config.max_results,
                )
                for source in k_config.sources:
                    if source.startswith(("http://", "https://")):
                        knowledge.insert(url=source)
                    elif Path(source).exists():
                        knowledge.insert(path=source)
                    else:
                        raise ValueError(
                            "Knowledge sources must be URLs or existing local paths. "
                            f"Got: {source}"
                        )
                return knowledge
                
        except ImportError as exc:
            raise ImportError(
                "Agno knowledge support requires optional vector-db dependencies. "
                "Install clawbridge[agno] with knowledge extras enabled."
            ) from exc
        return None

    def _compile_for_session(
        self,
        session_context: OpenClawSessionContext | None = None,
    ) -> Any:
        """
        Compile ClawAgent → Agno Agent.

        Agno agent structure (from their SDK):
            Agent(
                name=...,
                model=OpenAI(id="gpt-4o"),
                tools=[...],
                db=InMemoryDb(),
                knowledge=Knowledge(...),
                add_history_to_context=True,
                read_chat_history=True,
                instructions=[...],
                description=...,
                markdown=True,
            )
        """
        self._ensure_imports()
        Agent = self._agno_mod["Agent"]

        # Only pass our manual JSON memory if native storage is NOT enabled
        passed_memory = self.memory if not self.agent.storage.enabled else None
        system_prompt = self.build_system_prompt(
            passed_memory,
            session_context=session_context,
        )

        agent_kwargs: dict[str, Any] = {
            "name": self.agent.name,
            "model": self._resolve_model(),
            "description": self.agent.description,
            "instructions": [system_prompt],
            "markdown": self.agent.markdown_output,
        }

        # Tools
        tools = self._build_tools()
        if tools:
            agent_kwargs["tools"] = tools

        # Memory / Db
        agno_db = self._build_memory()
        if agno_db:
            agent_kwargs["db"] = agno_db
            agent_kwargs["add_history_to_context"] = True
            agent_kwargs["read_chat_history"] = True
            
        # Knowledge
        agno_knowledge = self._build_knowledge()
        if agno_knowledge:
            agent_kwargs["knowledge"] = agno_knowledge
            agent_kwargs["search_knowledge"] = self.agent.knowledge.search
            agent_kwargs["add_knowledge_to_context"] = self.agent.knowledge.add_to_context

        return Agent(**agent_kwargs)

    def compile(self) -> Any:
        """Compile the default main-session Agno agent."""
        self._native_agent = self._compile_for_session()
        return self._native_agent

    async def run(self, message: str, session_id: str = "default") -> str:
        """Run a message through the Agno agent."""
        session_context = self.get_session_context(session_id)
        agent = self._compile_for_session(session_context)

        # Track in our manual memory only if native storage is disabled
        if not self.agent.storage.enabled:
            self.memory.add_message(session_id, "user", message)

        # Use arun for async execution in Agno, passing the session_id
        response = await agent.arun(message, session_id=session_id)

        # Extract content from Agno's response
        content = self._extract_content(response)

        if not self.agent.storage.enabled:
            self.memory.add_message(session_id, "assistant", content)
            
        return content

    @staticmethod
    def _extract_content(response: Any) -> str:
        """Extract text content from Agno's RunResponse."""
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)

    def _build_interfaces(self) -> list[Any]:
        """Convert ChannelConfigs to Agno Interfaces."""
        interfaces: list[Any] = []
        native_agent = self.native
        for channel in self.agent.channels:
            try:
                if channel.type == "slack" and channel.token:
                    from agno.os.interfaces.slack import Slack
                    import os

                    signing_secret = (
                        os.environ.get(channel.verification_token_env)
                        if channel.verification_token_env
                        else None
                    )
                    interfaces.append(
                        Slack(
                            agent=native_agent,
                            token=channel.token,
                            signing_secret=signing_secret,
                        )
                    )
                elif channel.type == "whatsapp" and channel.token:
                    from agno.os.interfaces.whatsapp import Whatsapp
                    import os
                    verify_token = os.environ.get(channel.verification_token_env) if channel.verification_token_env else None
                    phone_number_id = os.environ.get(channel.bot_id_env) if channel.bot_id_env else None
                    interfaces.append(Whatsapp(
                        agent=native_agent,
                        access_token=channel.token,
                        verify_token=verify_token,
                        phone_number_id=phone_number_id
                    ))
            except ImportError as exc:
                raise ImportError(
                    f"Agno interface support for '{channel.type}' requires optional dependencies."
                ) from exc
        return interfaces

    async def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Serve as a FastAPI endpoint using Agno's AgentOS.
        """
        self._ensure_imports()
        AgentOS = self._agno_mod["AgentOS"]

        agent = self.native
        interfaces = self._build_interfaces()
        
        agent_os = AgentOS(
            agents=[agent],
            interfaces=interfaces if interfaces else None
        )
        app = agent_os.get_app()

        # AgentOS.serve uses uvicorn.run which is blocking.
        import asyncio
        import functools

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            functools.partial(agent_os.serve, app=app, host=host, port=port),
        )
