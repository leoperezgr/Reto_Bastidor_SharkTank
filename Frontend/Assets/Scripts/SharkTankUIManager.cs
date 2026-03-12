using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SharkTankUIManager : MonoBehaviour
{
    [SerializeField] private ApiClient apiClient;
    [SerializeField] private DialogueManager dialogueManager;

    // Expuesto para que DialogueManager pueda leerlo
    public string CurrentSessionId { get; private set; }
    public bool CanReply { get; private set; }

    public void StartPitch(string mode, string pitchText)
    {
        StartSessionRequest request = new StartSessionRequest
        {
            entrepreneur_name = dialogueManager.GetEntrepreneurName(),
            mode = mode,
            pitch = pitchText,
            business_idea = dialogueManager.GetBusinessIdea(),
            judges = dialogueManager.GetSelectedJudges()
        };

        apiClient.StartSession(request, OnSessionStarted, OnApiError);
    }

    public void SendUserReply(string message)
    {
        if (string.IsNullOrEmpty(CurrentSessionId))
        {
            Debug.LogError("No hay sesión activa.");
            return;
        }

        NextTurnRequest request = new NextTurnRequest
        {
            session_id = CurrentSessionId,
            user_message = message
        };

        apiClient.NextTurn(request, OnNextTurnReceived, OnApiError);
    }

    private void OnSessionStarted(SessionTurnResponse response)
    {
        Debug.Log("Sesión iniciada.");
        HandleResponse(response);
    }

    private void OnNextTurnReceived(SessionTurnResponse response)
    {
        Debug.Log("Turno recibido.");
        HandleResponse(response);
    }

    private void HandleResponse(SessionTurnResponse response)
    {
        CurrentSessionId = response.session_id;
        CanReply = response.conversation_status == "awaiting_response";

        Debug.Log($"Scene: {response.scene} | Status: {response.conversation_status}");

        // Pasar los mensajes al DialogueManager para que los muestre con sprites
        dialogueManager.DisplayMessages(response.messages);
    }

    private void OnApiError(string error)
    {
        Debug.LogError($"API Error: {error}");
        CanReply = true;
    }
}