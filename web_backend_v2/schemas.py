"""Pydantic schemas for the web backend."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ConversationMessageModel(BaseModel):
    role: str
    content: str


class QuestionStatusModel(BaseModel):
    question: str
    status: str
    response: str = ""
    timestamp: str = ""
    tokens_used: int = Field(default=0, alias="tokensUsed")
    processing_time: float = Field(default=0.0, alias="processingTime")
    model_used: str = Field(default="", alias="modelUsed")

    model_config = ConfigDict(populate_by_name=True)


class ConversationSummaryModel(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    provider: str
    selected_model: str = Field(alias="selectedModel")
    selected_directory: str = Field(alias="selectedDirectory")
    selected_files: List[str] = Field(alias="selectedFiles")
    persistent_files: List[str] = Field(alias="persistentFiles")
    question_history: List[QuestionStatusModel] = Field(alias="questionHistory")
    conversation_history: List[ConversationMessageModel] = Field(alias="conversationHistory")

    model_config = ConfigDict(populate_by_name=True)


class ConversationCreateRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = Field(default=None, alias="apiKey")

    model_config = ConfigDict(populate_by_name=True)


class ConversationCreateResponse(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    provider: str
    model: str
    available_models: List[str] = Field(alias="availableModels")
    summary: ConversationSummaryModel

    model_config = ConfigDict(populate_by_name=True)


class ConversationIdResponse(BaseModel):
    conversation_id: str = Field(alias="conversationId")


class AskQuestionRequest(BaseModel):
    question: str
    selected_files: Optional[List[str]] = Field(default=None, alias="selectedFiles")
    persistent: bool = False

    model_config = ConfigDict(populate_by_name=True)


class AskQuestionResponse(BaseModel):
    rawResponse: str = Field(alias="rawResponse")
    response: str
    processing_time: float = Field(alias="processingTime")
    tokens_used: int = Field(alias="tokensUsed")
    question_index: int = Field(alias="questionIndex")
    summary: ConversationSummaryModel

    model_config = ConfigDict(populate_by_name=True)


class SystemPromptResponse(BaseModel):
    response: str
    processing_time: float = Field(alias="processingTime")
    tokens_used: int = Field(alias="tokensUsed")
    summary: ConversationSummaryModel

    model_config = ConfigDict(populate_by_name=True)


class SetDirectoryRequest(BaseModel):
    path: str


class SetDirectoryResponse(BaseModel):
    directory: str
    files: List[dict]
    message: str
    summary: ConversationSummaryModel


class UpdateFilesRequest(BaseModel):
    selected_files: List[str] = Field(alias="selectedFiles")
    persistent: bool = False

    model_config = ConfigDict(populate_by_name=True)


class ExportConversationResponse(BaseModel):
    summary: ConversationSummaryModel


class ImportConversationRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    conversation_history: List[ConversationMessageModel] = Field(alias="conversationHistory")
    question_history: List[QuestionStatusModel] = Field(alias="questionHistory")
    selected_files: List[str] = Field(default_factory=list, alias="selectedFiles")
    persistent_files: List[str] = Field(default_factory=list, alias="persistentFiles")
    selected_directory: Optional[str] = Field(default=None, alias="selectedDirectory")

    model_config = ConfigDict(populate_by_name=True)


class SettingsUpdateRequest(BaseModel):
    updates: dict


class SystemMessageUpdateRequest(BaseModel):
    filename: str
    content: str


class SystemMessageSetRequest(BaseModel):
    filename: str


class FileContentRequest(BaseModel):
    files: List[str]


class FileContentResponse(BaseModel):
    combined_content: str = Field(alias="combinedContent")


class DirectoryScanRequest(BaseModel):
    path: str


class DirectoryScanResponse(BaseModel):
    directory: str
    files: List[dict]
    tree: dict


class ThemeToggleResponse(BaseModel):
    theme: str
    message: str


class ThemeSetRequest(BaseModel):
    theme: str


class UpdateModelRequest(BaseModel):
    model: str


class UpdateProviderRequest(BaseModel):
    provider: str
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    models: Optional[List[str]] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateApiKeyRequest(BaseModel):
    api_key: str = Field(alias="apiKey")

    model_config = ConfigDict(populate_by_name=True)


class FolderInfo(BaseModel):
    path: str
    fileCount: int


class FolderFileCountRequest(BaseModel):
    path: str


class FolderFileCountResponse(BaseModel):
    folders: List[FolderInfo]


class TopFoldersResponse(BaseModel):
    folders: List[str]
