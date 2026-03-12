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
    public Sprite financialHawkSprite;   // agent_id: "financial_hawk"
    public Sprite techVisionarySprite;   // agent_id: "tech_visionary"
    public Sprite theSharkSprite;        // agent_id: "the_shark"

    [Header("UI Panels")]
    public GameObject pitchPanel;
    public GameObject dialogueBox;

    [Header("Input")]
    public TMP_InputField pitchInput;
    public Button sendButton;

    [Header("Paginación")]
    public Button nextButton;
    private bool isWaitingForNextPage = false;

    [Header("Settings")]
    public float delayBetweenMessages = 2f;

    // Cola de mensajes pendientes de mostrar
    private Queue<AgentMessage> messageQueue = new Queue<AgentMessage>();
    private bool isShowingMessages = false;

    // Referencia al manager principal
    private SharkTankUIManager uiManager;

    void Start()
    {
        dialogueBox.SetActive(false);
        pitchPanel.SetActive(true);

        uiManager = FindObjectOfType<SharkTankUIManager>();

        if (sendButton != null)
            sendButton.onClick.AddListener(OnSendClicked);

        // NUEVO: Escuchar al botón Next
        if (nextButton != null)
            nextButton.onClick.AddListener(OnNextClicked);
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

            uiManager.StartPitch();
        }
        else
        {
            // Turnos siguientes: enviar respuesta del entrepreneur
            if (sendButton != null) sendButton.interactable = false;
            uiManager.SendUserReply(pitch);

            if (pitchInput != null) pitchInput.text = "";
        }
    }

    // Recibe la lista de mensajes del API y los encola
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
            case "financial_hawk":  return financialHawkSprite;
            case "tech_visionary":  return techVisionarySprite;
            case "the_shark":       return theSharkSprite;
            default:
                Debug.LogWarning($"No sprite encontrado para agent_id: {agentId}");
                return null;
        }
    }
}