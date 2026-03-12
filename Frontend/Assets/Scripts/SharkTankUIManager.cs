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

    public void StartPitch()
    {
        StartSessionRequest request = new StartSessionRequest
        {
            entrepreneur_name = "Carlos",
            mode = "normal",
            business_idea = new BusinessIdeaData
            {
                name = "SharkLab AI",
                description = "Simulador multiagente para practicar pitches",
                target_market = "Universidades e incubadoras",
                revenue_model = "Licencias SaaS",
                current_traction = "MVP funcional",
                investment_needed = "$150,000",
                use_of_funds = "Producto y expansión"
            },
            judges = new List<JudgeDefinition>
            {
                new JudgeDefinition
                {
                    id = "financial_hawk",
                    name = "Victoria Cross",
                    role = "Venture Capitalist & Financial Expert",
                    goal = "Identify investments with solid unit economics and a clear path to profitability",
                    backstory = "Numbers-focused investor"
                },
                new JudgeDefinition
                {
                    id = "tech_visionary",
                    name = "Nadia Osei",
                    role = "Deep Tech Investor & Former CTO",
                    goal = "Identify technology with genuine defensibility and the engineering team to scale it",
                    backstory = "Technical and scalability-focused investor"
                },
                new JudgeDefinition
                {
                    id = "the_shark",
                    name = "Mark Cuban",
                    role = "Serial Entrepreneur & Growth-Stage Investor",
                    goal = "Back relentlessly competitive founders who will outwork and out-execute everyone in their market",
                    backstory = "High-energy, sales-driven investor focused on hustle, competition, and execution."
                }
            }
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