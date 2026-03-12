# README - FrontEnd

Este proyecto es una aplicación de Unity que simula una sesión de "Shark Tank" (tanque de tiburones) interactiva. Permite a un emprendedor practicar pitches ante jueces virtuales impulsados por IA, utilizando un backend API para manejar la lógica de conversación multiagente.

El frontend de Unity maneja la interfaz de usuario, las llamadas a la API y la representación de mensajes de los agentes. Los scripts están diseñados para crear y gestionar GameObjects en Unity, ya que la escena no está completamente configurada aún.

## ¿Qué hace cada script?

### ApiClient.cs
Este script maneja todas las comunicaciones con el backend API. Incluye métodos para iniciar una nueva sesión de pitch (`StartSession`) y enviar turnos siguientes con mensajes del usuario (`NextTurn`). Utiliza UnityWebRequest para enviar solicitudes POST JSON y procesar respuestas. Es el puente entre Unity y el servidor backend corriendo en localhost:8000.

### SharkTankApiModels.cs
Define todas las clases de datos serializables utilizadas para las solicitudes y respuestas de la API. Incluye modelos como `StartSessionRequest`, `NextTurnRequest`, `SessionTurnResponse`, `AgentMessage`, etc. Estas clases permiten serializar/deserializar JSON para interactuar con el backend.

### SharkTankUIManager.cs
Es el gestor principal de la interfaz de usuario. Maneja el inicio de sesiones, el envío de respuestas del usuario y la representación de mensajes en los paneles de agentes. Contiene lógica para mapear agentes a paneles UI y actualizar el estado de la sesión. Incluye métodos como `StartPitch`, `SendUserReply` y `RenderMessages`.

### AgentPanelUI.cs
Representa un panel individual para cada agente (juez o emprendedor). Muestra el nombre del agente, el mensaje de texto y opcionalmente una imagen de retrato. Tiene métodos para establecer mensajes (`SetMessage`) y limpiar el panel (`Clear`). Cada instancia está asociada a un `agentId` específico.

### DemoBootstrap.cs
Script de arranque para la demostración. Se ejecuta al inicio de la escena y automáticamente inicia una sesión de pitch llamando a `StartPitch` en el `SharkTankUIManager`. Es útil para probar el flujo sin intervención manual.

## Cómo aplicarlo en Unity

### Paso 1: Configurar la escena
1. Abre Unity y carga el proyecto desde `Frontend/`.
2. Crea una nueva escena o usa `SampleScene.unity` en `Assets/Scenes/`.
3. Asegúrate de que tienes un Canvas en la escena para la UI (si no, crea uno: GameObject > UI > Canvas).

### Paso 2: Crear GameObjects y asignar scripts
1. **ApiClient GameObject**:
   - Crea un GameObject vacío (GameObject > Create Empty).
   - Nómbralo "ApiClient".
   - Agrega el script `ApiClient.cs` como componente.
   - En el Inspector, configura `Base Url` si es necesario (por defecto es "http://localhost:8000").

2. **SharkTankUIManager GameObject**:
   - Crea otro GameObject vacío y nómbralo "SharkTankUIManager".
   - Agrega el script `SharkTankUIManager.cs`.
   - En el Inspector:
     - Asigna el `ApiClient` creado al campo `Api Client`.
     - Crea o asigna un `InputField` para `User Input Field` (GameObject > UI > Input Field).
     - Crea o asigna un `Button` para `Send Button` (GameObject > UI > Button), y en su OnClick, llama a `SharkTankUIManager.SendUserReply`.
     - Para `Agent Panels`, necesitarás crear paneles para cada agente.

3. **Crear AgentPanelUI GameObjects**:
   - Para cada agente (ej. "entrepreneur", "financial_hawk", "tech_visionary"), crea un GameObject vacío o un Panel UI (GameObject > UI > Panel).
   - Agrega el script `AgentPanelUI.cs` a cada uno.
   - En el Inspector de cada `AgentPanelUI`:
     - Establece `Agent Id` al ID correspondiente (ej. "financial_hawk").
     - Asigna `Agent Name Text` a un Text UI child.
     - Asigna `Message Text` a otro Text UI child.
     - Opcional: Asigna `Portrait Image` a una Image UI.
   - Agrega estos `AgentPanelUI` a la lista `Agent Panels` en `SharkTankUIManager`.

4. **DemoBootstrap GameObject**:
   - Crea un GameObject vacío y nómbralo "DemoBootstrap".
   - Agrega el script `DemoBootstrap.cs`.
   - En el Inspector, asigna el `SharkTankUIManager` al campo correspondiente.

### Paso 3: Configurar la UI
- Asegúrate de que todos los elementos UI (Text, InputField, Button, Panels) estén correctamente posicionados en el Canvas.
- Para los paneles de agentes, organízalos en una layout apropiada (ej. horizontal o vertical).

### Paso 4: Ejecutar el proyecto
1. Asegúrate de que el backend esté corriendo en localhost:8000 (consulta el README del backend en `backend/`).
2. Presiona Play en Unity.
3. La escena debería iniciar automáticamente la sesión de pitch gracias a `DemoBootstrap`.
4. Usa el InputField para enviar mensajes y observa cómo se actualizan los paneles de agentes.

### Notas adicionales
- Los scripts usan Unity's UI system (Text, InputField, Button, Image). Asegúrate de tener el paquete TextMeshPro instalado si usas TMP components.
- Para producción, considera manejar errores de red y estados de carga.
- Los datos de la sesión están hardcodeados en `StartPitch` para demo; en un proyecto real, obténlos de inputs del usuario.
- Si encuentras errores, revisa la consola de Unity y el backend logs.