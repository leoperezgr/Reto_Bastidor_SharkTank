# Shark Tank AI Simulator - Version Final

> Esta es la version final del proyecto. Todos los features han sido implementados y probados.

## Descripcion del Proyecto

Aplicacion full-stack que simula una sesion interactiva de "Shark Tank". Un emprendedor presenta su pitch ante jueces virtuales impulsados por IA (Google Gemini + CrewAI), quienes hacen preguntas, debaten entre si y emiten veredictos. El frontend en Unity maneja la interfaz visual y el backend en Python/FastAPI orquesta la logica multiagente.

## Arquitectura

```
Usuario (Unity) → ApiClient → FastAPI Backend → CrewAI Agents (Gemini) → Respuestas de Jueces → Unity UI
```

- **Backend**: Python FastAPI + CrewAI + Google Gemini
- **Frontend**: Unity (C#) con TextMeshPro
- **Comunicacion**: REST API (JSON sobre HTTP)

## Estructura del Proyecto

```
Reto_Bastidor_SharkTank/
├── backend/
│   ├── main.py              # Servidor FastAPI, endpoints y logica de sesion
│   ├── judges_config.py     # Perfiles de jueces y modos de simulacion
│   ├── demo.py              # Demo interactiva por consola (Rich CLI)
│   ├── requirements.txt     # Dependencias Python
│   └── .env                 # Configuracion (API key, modelo, puerto)
├── Frontend/
│   └── Assets/
│       ├── Scripts/
│       │   ├── ApiClient.cs            # Cliente HTTP para comunicacion con backend
│       │   ├── SharkTankApiModels.cs   # Modelos de datos (request/response)
│       │   ├── SharkTankUIManager.cs   # Orquestador principal de UI y sesion
│       │   ├── DialogueManager.cs      # Sistema de dialogo, paginacion y cola de mensajes
│       │   ├── AgentPanelUI.cs         # Panel individual por agente/juez
│       │   └── TestDialogue.cs         # Utilidad de prueba
│       └── Scenes/
│           └── SampleScene.unity       # Escena principal
└── README.txt
```

## Jueces Disponibles (8)

| ID | Nombre | Rol |
|----|--------|-----|
| financial_hawk | Victoria Cross | Analista financiero implacable |
| market_maverick | Raj Patel | Experto en mercados y tendencias |
| tech_visionary | Nadia Osei | Visionaria tecnologica |
| operations_expert | James Chen | Experto en operaciones y escalabilidad |
| brand_guru | Sofia Martinez | Gurú de marca y marketing |
| the_perfectionist | Steve Jobs | El perfeccionista |
| the_disruptor | Elon Musk | El disruptor |
| the_oracle | Warren Buffett | El oraculo de las inversiones |

## Modos de Simulacion (5)

- **Quick**: Un veredicto decisivo rapido
- **Normal**: 2 rondas de preguntas/respuestas + veredicto
- **Full Tank**: 4 rondas de Q&A + negociacion
- **Rapid Fire**: Todos los jueces preguntan simultaneamente
- **Panel Debate**: Los jueces debaten entre si antes de emitir veredictos

## Endpoints del Backend

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | /api/session/start | Iniciar nueva sesion de pitch |
| POST | /api/session/next-turn | Enviar respuesta y obtener feedback |
| GET | /api/modes | Listar modos de simulacion |
| GET | /api/judges | Listar jueces disponibles |
| POST | /api/test-connection | Probar conectividad con Gemini |
| POST | /api/reset | Reiniciar sesiones |

## Como Ejecutar

### Backend
```bash
cd backend
pip install -r requirements.txt
# Configurar .env con GEMINI_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend (Unity)
1. Abrir el proyecto `Frontend/` en Unity.
2. Cargar la escena `SampleScene.unity`.
3. Asegurarse de que el backend este corriendo en `localhost:8000`.
4. Presionar Play.

### Demo por Consola
```bash
cd backend
python demo.py
```

## Flujo de Uso

1. El usuario llena el formulario con los datos de su startup (nombre, descripcion, mercado, modelo de ingresos, etc.).
2. Selecciona los jueces y el modo de simulacion.
3. Escribe su pitch inicial y presiona "Send".
4. Los jueces responden con preguntas y comentarios (mostrados secuencialmente con paginacion).
5. El usuario responde a las preguntas.
6. Se repite hasta que la sesion termina con veredictos finales.

## Dependencias

### Backend
- fastapi, uvicorn
- crewai
- python-dotenv
- google-generativeai
- pydantic
- rich

### Frontend
- Unity (con TextMeshPro)
- Newtonsoft.Json (para serializacion)
