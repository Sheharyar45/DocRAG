from typing import List
from dataclasses import dataclass
import re
from transformers import AutoTokenizer

@dataclass
class Chunk:
    content: str
    chunk_index: int
    token_count: int
    metadata: dict


_tokenizer = None


def get_tokenizer():
    """Get or create tokenizer."""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-base-en-v1.5")
    return _tokenizer


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return len(get_tokenizer().encode(text, add_special_tokens=False))


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove Markdown headers (keep the text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove Markdown bold/italic
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
    # Remove Markdown links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove Markdown images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove inline code backticks
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # or newline boundaries
    sentence_pattern = (
        r'(?<=[.!?])'       # after sentence-ending punctuation
        r'(?<!\b\w\.)'       # not after single-letter abbreviation like "U."
        r'\s+'               # whitespace
        r'(?=[A-Z"\'])'      # before uppercase letter or quote (new sentence)
    )
    sentences = re.split(sentence_pattern, text)
    
    # Also split on double newlines (paragraph boundaries)
    final_sentences = []
    for s in sentences:
        parts = re.split(r'\n{2,}', s)
        final_sentences.extend([p.strip() for p in parts if p.strip()])
    
    return final_sentences


def chunk_by_sentences(
    text: str,
    max_tokens: int = 300,
    overlap_sentences: int = 2
) -> List[Chunk]:
    """
    Split text into chunks by sentences with token-based sizing.
    Uses sentence-based overlap for better context preservation.
    """
    text = clean_text(text)
    
    if not text:
        return []
    
    sentences = split_into_sentences(text)
    
    if not sentences:
        return []
    
    chunks = []
    current_sentences: List[str] = []
    current_tokens = 0
    chunk_index = 0
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        
        # If single sentence exceeds max, it becomes its own chunk
        if sentence_tokens > max_tokens:
            # Save current chunk if exists
            if current_sentences:
                chunk_content = " ".join(current_sentences)
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    metadata={}
                ))
                chunk_index += 1
            
            # Add long sentence as its own chunk
            chunks.append(Chunk(
                content=sentence,
                chunk_index=chunk_index,
                token_count=sentence_tokens,
                metadata={}
            ))
            chunk_index += 1
            current_sentences = []
            current_tokens = 0
            continue
        
        # If adding this sentence exceeds max, save current chunk
        if current_tokens + sentence_tokens > max_tokens and current_sentences:
            chunk_content = " ".join(current_sentences)
            chunks.append(Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                token_count=current_tokens,
                metadata={}
            ))
            chunk_index += 1
            
            # Sentence-based overlap: keep last N sentences
            if overlap_sentences > 0 and len(current_sentences) >= overlap_sentences:
                overlap = current_sentences[-overlap_sentences:]
                current_sentences = overlap.copy()
                current_tokens = count_tokens(" ".join(current_sentences))
            else:
                current_sentences = []
                current_tokens = 0
        
        current_sentences.append(sentence)
        current_tokens = count_tokens(" ".join(current_sentences))
    
    # Don't forget the last chunk
    if current_sentences:
        chunk_content = " ".join(current_sentences)
        chunks.append(Chunk(
            content=chunk_content,
            chunk_index=chunk_index,
            token_count=count_tokens(chunk_content),
            metadata={}
        ))
    
    return chunks


def chunk_note(
    note_id: str,
    title: str,
    content: str,
    folder_id: str = None,
    max_tokens: int = 300,
    overlap_sentences: int = 2,
    tags: List[str] = []
) -> List[Chunk]:
    """
    Chunk a note with metadata attached to each chunk.
    Title is stored in metadata, not prepended to content.
    """
    chunks = chunk_by_sentences(content, max_tokens, overlap_sentences)
    context_prefix = f"Title: {title}."
    if tags:
        context_prefix += f" Tags: {', '.join(tags)}."
    
    # Add note metadata to each chunk
    for chunk in chunks:
        chunk.content = f"{context_prefix}\n\n{chunk.content}"
        chunk.token_count = count_tokens(chunk.content)
        chunk.metadata = {
            "note_id": note_id,
            "title": title,
            "tags": tags,
            "folder_id": folder_id,
            "chunk_index": chunk.chunk_index,
            "total_chunks": len(chunks)
        }
    
    return chunks