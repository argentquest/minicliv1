"""System message helpers for the web backend."""
from __future__ import annotations

from typing import Dict, List, Optional

from common.system_message_manager import system_message_manager
from common.logger import get_logger

logger = get_logger(__name__)


class SystemMessageService:
    """Adapter around system_message_manager for REST usage."""

    def list_messages(self) -> List[Dict[str, str]]:
        return system_message_manager.get_system_message_files_info()

    def get_current_file(self) -> str:
        logger.info("Getting current system message file")
        current_file = system_message_manager.current_message_file
        logger.info(f"Current system message: {current_file}")
        return current_file

    def load_message(self, filename: str) -> Optional[str]:
        return system_message_manager.load_custom_system_message(filename)

    def set_current(self, filename: str) -> bool:
        return system_message_manager.set_current_system_message_file(filename)

    def save(self, filename: str, content: str) -> bool:
        system_message_manager.system_message_file = filename
        return system_message_manager.save_custom_system_message(content)

    def delete(self, filename: str) -> bool:
        system_message_manager.system_message_file = filename
        return system_message_manager.delete_custom_system_message()


system_message_service = SystemMessageService()
