using UnityEngine;
using TMPro;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;

public class DialogueManager : MonoBehaviour
{
    [Header("UI References")]
    public TextMeshProUGUI dialogueText;
    public TextMeshProUGUI speakerName;
    public Image sharkSpeaker;

    [Header("Sprites por Agent ID")]
    public Sprite financialHawkSprite;
    public Sprite techVisionarySprite;
    public Sprite theSharkSprite;
    public Sprite marketMaverickSprite;
    public Sprite operationsExpertSprite;
    public Sprite brandGuruSprite;
    public Sprite thePerfectionistSprite;
    public Sprite theDisruptorSprite;
    public Sprite theOracleSprite;

    [Header("Judge Selection")]
    public Transform judgeToggleContainer;
    public GameObject judgeTogglePrefab;

    [Header("UI Panels")]
    public GameObject pitchPanel;
    public GameObject dialogueBox;

    [Header("Business Idea Form")]
    public TMP_InputField entrepreneurNameInput;
    public TMP_InputField businessNameInput;
    public TMP_InputField descriptionInput;
    public TMP_InputField targetMarketInput;
    public TMP_InputField revenueModelInput;
    public TMP_InputField currentTractionInput;
    public TMP_InputField investmentNeededInput;
    public TMP_InputField useOfFundsInput;

    [Header("Input")]
    public TMP_InputField pitchInput;
    public Button sendButton;

    [Header("Mode Selection")]
    public TMP_Dropdown modeDropdown;

    [Header("Paginación")]
    public Button nextButton;
    private bool isWaitingForNextPage = false;

    [Header("Settings")]
    public float delayBetweenMessages = 2f;

    // Cola de mensajes pendientes de mostrar
    private Queue<AgentMessage> messageQueue = new Queue<AgentMessage>();
    private bool isShowingMessages = false;
    private List<string> modeKeys = new List<string>();

    // Jueces disponibles cargados del backend
    private List<JudgeDefinition> availableJudges = new List<JudgeDefinition>();
    private List<Toggle> judgeToggles = new List<Toggle>();

    // Referencia al manager principal
    private SharkTankUIManager uiManager;
    private ApiClient apiClient;

    void Start()
    {
        dialogueBox.SetActive(false);
        pitchPanel.SetActive(true);

        uiManager = FindFirstObjectByType<SharkTankUIManager>();
        apiClient = FindFirstObjectByType<ApiClient>();

        if (sendButton != null)
            sendButton.onClick.AddListener(OnSendClicked);

        // NUEVO: Escuchar al botón Next
        if (nextButton != null)
            nextButton.onClick.AddListener(OnNextClicked);

        // Cargar modos y jueces del backend
        if (apiClient != null)
        {
            apiClient.GetModes(OnModesReceived, (err) => Debug.LogWarning($"No se pudieron cargar los modos: {err}"));
            apiClient.GetJudges(OnJudgesReceived, (err) => Debug.LogWarning($"No se pudieron cargar los jueces: {err}"));
        }
    }

    // Llamado cuando el usuario presiona Send / Start Pitch
    private void OnSendClicked()
    {
        string pitch = pitchInput != null ? pitchInput.text.Trim() : "";

        if (string.IsNullOrEmpty(pitch))
        {
            Debug.LogWarning("El pitch está vacío.");
            return;
        }

        // Primera vez: iniciar sesión
        if (string.IsNullOrEmpty(uiManager.CurrentSessionId))
        {
            pitchPanel.SetActive(false);
            dialogueBox.SetActive(true);

            if (sendButton != null) sendButton.interactable = false;

            uiManager.StartPitch(GetSelectedMode(), pitch);
        }
        else
        {
            // Turnos siguientes: enviar respuesta del entrepreneur
            // 2. NUEVO: Volver a intercambiar los paneles
            if (pitchPanel != null) pitchPanel.SetActive(false);
            if (dialogueBox != null) dialogueBox.SetActive(true);

            if (sendButton != null) sendButton.interactable = false;
            uiManager.SendUserReply(pitch);

            if (pitchInput != null) pitchInput.text = "";
        }
    }

    // ===== Dropdown de modos =====

    private void OnModesReceived(Dictionary<string, string> modes)
    {
        if (modeDropdown == null) return;

        modeDropdown.ClearOptions();
        modeKeys.Clear();

        var options = new List<string>();
        foreach (var mode in modes)
        {
            modeKeys.Add(mode.Key);
            options.Add(mode.Value);
        }

        modeDropdown.AddOptions(options);
        Debug.Log($"Modos cargados: {modeKeys.Count}");
    }

    public string GetSelectedMode()
    {
        if (modeKeys.Count == 0 || modeDropdown == null) return "normal";
        return modeKeys[modeDropdown.value];
    }

    // ===== Jueces =====

    private void OnJudgesReceived(List<JudgeDefinition> judges)
    {
        availableJudges = judges;
        Debug.Log($"Jueces cargados: {judges.Count}");

        if (judgeToggleContainer == null || judgeTogglePrefab == null) return;

        // Limpiar toggles anteriores
        foreach (Transform child in judgeToggleContainer)
            Destroy(child.gameObject);
        judgeToggles.Clear();

        foreach (var judge in judges)
        {
            GameObject toggleObj = Instantiate(judgeTogglePrefab, judgeToggleContainer);
            Toggle toggle = toggleObj.GetComponent<Toggle>();
            TextMeshProUGUI label = toggleObj.GetComponentInChildren<TextMeshProUGUI>();

            if (label != null)
                label.text = $"{judge.name} - {judge.role}";

            toggle.isOn = false;
            judgeToggles.Add(toggle);
        }
    }

    public List<JudgeDefinition> GetSelectedJudges()
    {
        var selected = new List<JudgeDefinition>();

        for (int i = 0; i < judgeToggles.Count && i < availableJudges.Count; i++)
        {
            if (judgeToggles[i].isOn)
                selected.Add(availableJudges[i]);
        }

        // Si no seleccionó ninguno, usar los primeros 3
        if (selected.Count == 0 && availableJudges.Count > 0)
        {
            Debug.LogWarning("No se seleccionaron jueces, usando los primeros 3.");
            for (int i = 0; i < Mathf.Min(3, availableJudges.Count); i++)
                selected.Add(availableJudges[i]);
        }

        return selected;
    }

    public string GetEntrepreneurName()
    {
        string name = entrepreneurNameInput != null ? entrepreneurNameInput.text.Trim() : "";
        return string.IsNullOrEmpty(name) ? "Emprendedor" : name;
    }

    public BusinessIdeaData GetBusinessIdea()
    {
        return new BusinessIdeaData
        {
            name = businessNameInput != null ? businessNameInput.text.Trim() : "Mi Startup",
            description = descriptionInput != null ? descriptionInput.text.Trim() : "",
            target_market = targetMarketInput != null ? targetMarketInput.text.Trim() : "",
            revenue_model = revenueModelInput != null ? revenueModelInput.text.Trim() : "",
            current_traction = currentTractionInput != null ? currentTractionInput.text.Trim() : "",
            investment_needed = investmentNeededInput != null ? investmentNeededInput.text.Trim() : "",
            use_of_funds = useOfFundsInput != null ? useOfFundsInput.text.Trim() : ""
        };
    }

    // ===== Mostrar mensajes =====
    public void DisplayMessages(List<AgentMessage> messages)
    {
        foreach (var msg in messages)
            messageQueue.Enqueue(msg);

        if (!isShowingMessages)
            StartCoroutine(ShowQueuedMessages());
    }

    private IEnumerator ShowQueuedMessages()
    {
        isShowingMessages = true;
        if (nextButton != null) nextButton.gameObject.SetActive(true);

        while (messageQueue.Count > 0)
        {
            AgentMessage msg = messageQueue.Dequeue();
            ShowMessage(msg);

            // 1. EL TRUCO: Esperar un frame exacto para que TextMeshPro acomode el texto
            yield return null; 

            // 2. Ahora sí, forzar la actualización y contar las páginas
            dialogueText.ForceMeshUpdate();
            int totalPages = dialogueText.textInfo.pageCount;
            dialogueText.pageToDisplay = 1;

            // ESTO NOS DIRÁ EN LA CONSOLA SI CALCULÓ BIEN
            Debug.Log($"[Paginación] Texto de {msg.agent_name}. Total de páginas calculadas: {totalPages}");

            while (dialogueText.pageToDisplay <= totalPages)
            {
                isWaitingForNextPage = true;
                
                yield return new WaitUntil(() => !isWaitingForNextPage);

                if (dialogueText.pageToDisplay < totalPages)
                {
                    dialogueText.pageToDisplay++;
                }
                else
                {
                    break; 
                }
            }
    }

    if (nextButton != null) nextButton.gameObject.SetActive(false);
    isShowingMessages = false;

    bool canReply = uiManager.CanReply;
    // 1. NUEVO: Reactivar el panel visualmente para el Round 2
    if (canReply)
    {
        if (pitchPanel != null) pitchPanel.SetActive(true);
        
        // Ocultar la caja de diálogo de los tiburones para despejar la pantalla
        if (dialogueBox != null) dialogueBox.SetActive(false); 
    }

    if (pitchInput != null) pitchInput.interactable = canReply;
    if (sendButton != null) sendButton.interactable = canReply;
}

    public void OnNextClicked()
    {
        // MENSAJE DE PRUEBA PARA SABER SI EL BOTÓN REALMENTE FUNCIONA
        Debug.Log("[Botón] Se presionó NEXT");

        if (isWaitingForNextPage)
        {
            isWaitingForNextPage = false;
        }
}

    private void ShowMessage(AgentMessage msg)
    {
        dialogueText.text = msg.text;
        speakerName.text = msg.agent_name;
        sharkSpeaker.sprite = GetSpriteForAgent(msg.agent_id);

        Debug.Log($"[DialogueManager] Mostrando: {msg.agent_name} -> {msg.text}");
    }

    private Sprite GetSpriteForAgent(string agentId)
    {
        switch (agentId)
        {
            case "financial_hawk":     return financialHawkSprite;
            case "tech_visionary":     return techVisionarySprite;
            case "the_shark":          return theSharkSprite;
            case "market_maverick":    return marketMaverickSprite;
            case "operations_expert":  return operationsExpertSprite;
            case "brand_guru":         return brandGuruSprite;
            case "the_perfectionist":  return thePerfectionistSprite;
            case "the_disruptor":      return theDisruptorSprite;
            case "the_oracle":         return theOracleSprite;
            default:
                Debug.LogWarning($"No sprite encontrado para agent_id: {agentId}");
                return null;
        }
    }
}