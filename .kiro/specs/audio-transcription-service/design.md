# Design Document - Audio Transcription Service

## Overview

O Audio Transcription Service é uma aplicação web containerizada que permite upload de arquivos de áudio e retorna transcrições em texto usando o modelo Whisper da OpenAI executado localmente. A arquitetura é composta por um backend Python (Flask/FastAPI) que gerencia uploads e processa transcrições, e um frontend simples em HTML/JavaScript para interação do usuário.

O sistema utiliza a biblioteca `openai-whisper` (ou `faster-whisper` para melhor performance) executada localmente dentro de um container Docker, eliminando a necessidade de chamadas a APIs externas. O modelo Whisper será baixado automaticamente na primeira execução e armazenado em um volume Docker para reutilização.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Web Browser   │
│   (Frontend)    │
└────────┬────────┘
         │ 1. POST /upload (returns task_id)
         │ 2. GET /status/{task_id} (polling every 2s)
         │ 3. GET /result/{task_id} (when completed)
         ▼
┌─────────────────┐
│     FastAPI     │
│   Web Server    │
├─────────────────┤
│ Background Tasks│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Whisper Service │
│  (Local Model)  │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  SQLite Store   │
│  (Task State)   │
└─────────────────┘
```

### Container Architecture

```
Docker Compose
├── transcription-service (FastAPI)
│   ├── Handles HTTP requests
│   ├── File upload management
│   ├── Background task processing
│   ├── SQLite for task state
│   ├── Whisper model integration
│   └── Serves static frontend
└── volumes
    ├── whisper-models (persisted model cache)
    ├── uploads (temporary audio files)
    └── database (SQLite file)
```

## Components and Interfaces

### 1. Frontend (HTML/JavaScript)

**Responsibilities:**
- Renderizar interface de upload
- Validar arquivos no client-side
- Exibir progresso de upload
- Mostrar resultado da transcrição
- Permitir download do arquivo .txt

**Interface:**
- Formulário de upload com drag-and-drop
- Indicador de progresso com polling
- Área de exibição de texto transcrito
- Botão de download
- Mensagens de status (processing, completed, failed)

**Polling Logic:**
```javascript
// Após upload bem-sucedido
const taskId = response.task_id;
const pollInterval = setInterval(async () => {
    const status = await fetch(`/api/status/${taskId}`);
    if (status.status === 'completed') {
        clearInterval(pollInterval);
        // Buscar resultado
        const result = await fetch(`/api/result/${taskId}`);
        // Exibir texto
    } else if (status.status === 'failed') {
        clearInterval(pollInterval);
        // Exibir erro
    }
}, 2000); // Poll a cada 2 segundos
```

### 2. Web Server (FastAPI)

**Responsibilities:**
- Receber uploads de arquivos
- Validar tipo e tamanho de arquivo
- Gerenciar armazenamento temporário
- Iniciar processamento em background
- Gerenciar estado das transcrições
- Retornar resultados ao cliente
- Servir arquivos estáticos

**Endpoints:**

```
POST /api/upload
- Input: multipart/form-data com arquivo de áudio
- Output: JSON com task_id para polling
- Validações: tipo de arquivo, tamanho máximo
- Inicia background task e retorna imediatamente

GET /api/status/{task_id}
- Input: task_id da transcrição
- Output: JSON com status (processing/completed/failed)
- Permite polling do frontend

GET /api/result/{task_id}
- Input: task_id da transcrição completada
- Output: JSON com texto transcrito e metadados
- Retorna erro se ainda não completou

GET /api/download/{task_id}
- Input: task_id da transcrição
- Output: arquivo .txt para download

GET /
- Serve a interface HTML
```

### 3. Whisper Service

**Responsibilities:**
- Carregar modelo Whisper na inicialização
- Processar arquivos de áudio de forma assíncrona
- Retornar texto transcrito
- Gerenciar recursos (memória, GPU se disponível)

**Interface:**
```python
class WhisperService:
    def __init__(self, model_size: str = "base"):
        # Carrega modelo faster-whisper (tiny, base, small, medium, large)
        # Usa CTranslate2 para melhor performance
        pass

    async def transcribe(self, audio_file_path: str) -> dict:
        # Retorna: {"text": "...", "language": "...", "duration": ...}
        # Executa em thread pool para não bloquear event loop
        pass
```

### 4. Task Store (SQLite)

**Responsibilities:**
- Persistir estado das tasks de transcrição
- Permitir consulta de status por task_id
- Armazenar resultados de transcrições
- Gerenciar limpeza de tasks antigas

**Schema:**
```sql
CREATE TABLE transcription_tasks (
    task_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_text TEXT,
    language TEXT,
    duration REAL
);
```

**Interface:**
```python
class TaskStore:
    def create_task(self, task_id: str, filename: str, file_path: str) -> None
    def update_status(self, task_id: str, status: str) -> None
    def save_result(self, task_id: str, text: str, language: str, duration: float) -> None
    def get_task(self, task_id: str) -> Optional[TranscriptionTask]
    def get_result(self, task_id: str) -> Optional[TranscriptionResult]
```

## Data Models

### TranscriptionTask
```python
{
    "task_id": str,  # UUID da task
    "status": str,  # "pending" | "processing" | "completed" | "failed"
    "filename": str,  # Nome original do arquivo
    "file_path": str,  # Caminho do arquivo no servidor
    "created_at": datetime,
    "started_at": Optional[datetime],
    "completed_at": Optional[datetime],
    "error_message": Optional[str]
}
```

### TranscriptionResult
```python
{
    "task_id": str,  # UUID da transcrição
    "text": str,  # Texto transcrito
    "language": str,  # Idioma detectado
    "duration": float,  # Duração do processamento em segundos
    "filename": str,  # Nome original do arquivo
    "completed_at": datetime
}
```

### UploadResponse
```python
{
    "task_id": str,  # UUID para polling
    "message": str,  # "Upload successful, processing started"
    "status_url": str  # URL para polling: /api/status/{task_id}
}
```

### StatusResponse
```python
{
    "task_id": str,
    "status": str,  # "pending" | "processing" | "completed" | "failed"
    "progress": Optional[int],  # Percentual (se disponível)
    "message": Optional[str]
}
```

### FileValidation
```python
{
    "allowed_extensions": [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"],
    "max_file_size_mb": 100,
    "mime_types": ["audio/mpeg", "audio/wav", "audio/x-m4a", "audio/ogg", "audio/webm", "audio/flac"]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

Após análise inicial, identifiquei as seguintes redundâncias:
- Propriedades 1.5 e 2.1 são redundantes (ambas testam que texto transcrito é retornado)
- Propriedades 3.3 e 3.4 podem ser combinadas (ambas testam tratamento de erro)
- Propriedades 3.1 e 3.2 podem ser combinadas em uma propriedade mais abrangente

### Core Properties

Property 1: Valid audio formats are accepted
*For any* arquivo com extensão válida (mp3, wav, m4a, ogg, webm, flac) e tamanho dentro do limite, o sistema deve aceitar o upload e processar a transcrição
**Validates: Requirements 1.2, 1.3**

Property 2: Invalid file types are rejected
*For any* arquivo com tipo MIME não-áudio ou extensão inválida, o sistema deve rejeitar o upload e retornar mensagem de erro apropriada
**Validates: Requirements 5.1**

Property 3: Oversized files are rejected
*For any* arquivo que excede o tamanho máximo configurado, o sistema deve rejeitar o upload e informar o limite ao usuário
**Validates: Requirements 5.2**

Property 4: Upload returns task ID immediately
*For any* arquivo de áudio válido, o endpoint de upload deve retornar um task_id imediatamente sem esperar o processamento completar
**Validates: Requirements 1.3, 1.5**

Property 5: Status polling reflects processing state
*For any* task_id válido, o endpoint de status deve retornar o estado atual correto (pending/processing/completed/failed)
**Validates: Requirements 1.5, 2.1**

Property 6: Transcription returns complete text
*For any* arquivo de áudio válido processado, o endpoint de resultado deve conter o texto completo da transcrição quando o status for completed
**Validates: Requirements 2.1, 3.1, 3.2**

Property 7: Download generates correct file
*For any* transcrição completada, o endpoint de download deve retornar um arquivo .txt contendo exatamente o texto transcrito
**Validates: Requirements 2.3**

Property 8: Download filename format
*For any* arquivo de download gerado, o nome deve conter um timestamp e terminar com extensão .txt
**Validates: Requirements 2.4**

Property 9: Validation occurs before processing
*For any* arquivo submetido, a validação de tipo e tamanho deve ocorrer antes de criar a task e invocar o Whisper Model, garantindo que arquivos inválidos não sejam processados
**Validates: Requirements 1.3**

Property 10: Errors are handled gracefully
*For any* erro durante o processamento (Whisper falha, arquivo corrompido, etc), o sistema deve capturar o erro, atualizar o status para "failed", registrar em log, e permitir consulta do erro via status endpoint
**Validates: Requirements 3.3, 3.4**

## Error Handling

### Error Categories

1. **Validation Errors (4xx)**
   - Invalid file type → 400 Bad Request
   - File too large → 413 Payload Too Large
   - Missing file → 400 Bad Request
   - Corrupted file → 400 Bad Request

2. **Processing Errors (5xx)**
   - Whisper model failure → 500 Internal Server Error
   - Model not loaded → 503 Service Unavailable
   - Out of memory → 507 Insufficient Storage

3. **System Errors**
   - Model loading failure → Application fails to start
   - Docker container issues → Container restart

### Error Response Format

```json
{
    "error": true,
    "message": "User-friendly error message",
    "code": "ERROR_CODE",
    "details": "Technical details (optional, for debugging)"
}
```

### Logging Strategy

- **INFO**: Successful transcriptions, service startup
- **WARNING**: Validation failures, rejected uploads
- **ERROR**: Processing failures, model errors
- **CRITICAL**: Service initialization failures

## Testing Strategy

### Unit Testing

O projeto utilizará **pytest** para testes unitários em Python. Os testes unitários focarão em:

- Validação de arquivos (tipo, tamanho, extensão)
- Formatação de nomes de arquivo
- Parsing de respostas do Whisper
- Tratamento de erros específicos
- Endpoints da API (usando TestClient do FastAPI/Flask)

### Property-Based Testing

O projeto utilizará **Hypothesis** para property-based testing em Python. A biblioteca será configurada para executar no mínimo 100 iterações por propriedade.

Cada teste de propriedade deve:
- Ser marcado com comentário referenciando a propriedade do design: `# Feature: audio-transcription-service, Property X: [texto da propriedade]`
- Gerar dados aleatórios apropriados (arquivos de teste, tamanhos, tipos)
- Verificar que a propriedade se mantém para todos os inputs gerados

Estratégias de geração de dados:
- Arquivos de áudio: gerar arquivos de teste com diferentes formatos e tamanhos
- Tipos MIME: gerar combinações válidas e inválidas
- Tamanhos de arquivo: gerar valores dentro e fora dos limites
- Nomes de arquivo: gerar strings com diferentes caracteres e formatos

### Integration Testing

Testes de integração verificarão:
- Container Docker inicia corretamente
- Modelo Whisper é carregado na inicialização
- Endpoints respondem após startup
- Upload e download funcionam end-to-end

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI (assíncrono, suporte nativo a background tasks)
- **Whisper Library**: `faster-whisper` (otimizado, usa CTranslate2, 4x mais rápido que openai-whisper)
- **Database**: SQLite com `sqlalchemy` ou `sqlmodel`
- **File Handling**: `python-multipart` para uploads
- **Async**: `asyncio` para processamento não-bloqueante
- **Testing**: pytest, pytest-asyncio, hypothesis

### Frontend
- **HTML5** com formulário de upload
- **JavaScript vanilla** para interação
- **CSS** para estilização básica

### Infrastructure
- **Docker** & **Docker Compose**
- **Base Image**: python:3.11-slim
- **Volume**: Para cache do modelo Whisper

### Model Configuration

- **Default Model**: `base` (boa relação qualidade/velocidade)
- **Alternative Models**: tiny, small, medium, large (configurável via env var)
- **Model Storage**: `/root/.cache/whisper` (volume persistido)

## Deployment Configuration

### Docker Compose Structure

```yaml
version: '3.8'

services:
  transcription-service:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - whisper-models:/root/.cache/whisper
      - uploads:/app/uploads
      - database:/app/data
    environment:
      - WHISPER_MODEL=base
      - MAX_FILE_SIZE_MB=100
      - ALLOWED_EXTENSIONS=mp3,wav,m4a,ogg,webm,flac
      - DATABASE_PATH=/app/data/transcriptions.db
      - CLEANUP_AFTER_HOURS=24

volumes:
  whisper-models:
  uploads:
  database:
```

### Environment Variables

- `WHISPER_MODEL`: Tamanho do modelo (tiny/base/small/medium/large) - default: base
- `MAX_FILE_SIZE_MB`: Tamanho máximo de arquivo em MB - default: 100
- `ALLOWED_EXTENSIONS`: Extensões permitidas (separadas por vírgula)
- `PORT`: Porta do serviço - default: 8000
- `DATABASE_PATH`: Caminho do arquivo SQLite - default: /app/data/transcriptions.db
- `CLEANUP_AFTER_HOURS`: Horas para manter arquivos/tasks antigas - default: 24

## Performance Considerations

### Model Selection Trade-offs

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| tiny  | 39M  | ~32x  | Basic   | Testing, demos |
| base  | 74M  | ~16x  | Good    | **Recommended for MVP** |
| small | 244M | ~6x   | Better  | Higher quality needed |
| medium| 769M | ~2x   | Great   | Professional use |
| large | 1550M| 1x    | Best    | Maximum quality |

### Resource Requirements

- **Minimum RAM**: 2GB (tiny/base models)
- **Recommended RAM**: 4GB (base/small models)
- **GPU**: Optional, mas acelera significativamente (CUDA support)
- **Disk Space**: 1-5GB (dependendo do modelo)

### Optimization Strategies

1. **faster-whisper**: Usa CTranslate2 para 4x mais velocidade que openai-whisper na CPU
2. **Model Caching**: Volume Docker persiste modelo baixado
3. **Background Tasks**: FastAPI BackgroundTasks para processamento não-bloqueante
4. **Thread Pool**: Whisper roda em thread pool para não bloquear event loop
5. **Polling**: Frontend usa polling em vez de conexão longa
6. **File Cleanup**: Remove arquivos temporários após período configurável
7. **SQLite**: Banco leve e sem necessidade de servidor separado

## Security Considerations

### File Upload Security

- Validação de tipo MIME (não apenas extensão)
- Limite de tamanho de arquivo
- Sanitização de nomes de arquivo
- Armazenamento temporário isolado
- Limpeza automática de arquivos antigos

### Container Security

- Execução como usuário não-root (quando possível)
- Volumes isolados
- Sem exposição de portas desnecessárias
- Logs sem informações sensíveis

## Processing Flow

### Upload Flow
1. User selects audio file in browser
2. Frontend validates file type/size (client-side)
3. POST /api/upload with multipart form data
4. Server validates file (server-side)
5. Server saves file to uploads directory
6. Server creates task in SQLite with status "pending"
7. Server starts background task
8. Server returns task_id immediately
9. Background task updates status to "processing"
10. Background task calls Whisper service
11. Whisper processes audio (may take minutes)
12. Background task saves result to SQLite
13. Background task updates status to "completed"

### Polling Flow
1. Frontend receives task_id from upload
2. Frontend starts polling GET /api/status/{task_id} every 2 seconds
3. Server returns current status from SQLite
4. When status is "completed", frontend stops polling
5. Frontend calls GET /api/result/{task_id}
6. Server returns transcription text
7. Frontend displays text and enables download button

### Download Flow
1. User clicks download button
2. Frontend calls GET /api/download/{task_id}
3. Server generates .txt file with timestamp in name
4. Browser downloads file

## Future Enhancements (Out of Scope for MVP)

- Suporte a múltiplos idiomas configuráveis via UI
- WebSocket para updates em tempo real (substituir polling)
- Histórico de transcrições com busca
- Autenticação de usuários
- Suporte a timestamps no texto (word-level timing)
- Detecção de múltiplos speakers (diarization)
- Interface web mais elaborada com React/Vue
- Suporte a GPU para processamento mais rápido
- Fila de prioridade para múltiplos uploads simultâneos
- Progress bar real baseado em progresso do Whisper
