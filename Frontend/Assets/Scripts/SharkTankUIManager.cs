using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SharkTankUIManager : MonoBehaviour
{
    [SerializeField] private ApiClient apiClient;
    [SerializeField] private List<AgentPanelUI> agentPanels;
    [SerializeField] private TMP_InputField userInputField;
    [SerializeField] private Button sendButton;

    private string currentSessionId;
    private int currentTurn;

    private Dictionary<string, AgentPanelUI> agentPanelMap = new Dictionary<string, AgentPanelUI>();

    private void Start()
    {
        foreach (var panel in agentPanels)
        {
            if (!string.IsNullOrEmpty(panel.AgentId))
            {
                agentPanelMap[panel.AgentId] = panel;
            }
        }

        if (sendButton != null)
            sendButton.onClick.AddListener(SendUserReply);
    }

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

    public void SendUserReply()
    {
        if (string.IsNullOrEmpty(currentSessionId))
        {
            Debug.LogError("No active session to send reply.");
            return;
        }

        string userMessage = userInputField != null ? userInputField.text.Trim() : "";

        if (string.IsNullOrEmpty(userMessage))
        {
            Debug.LogWarning("User message is empty.");
            return;
        }

        NextTurnRequest request = new NextTurnRequest
        {
            session_id = currentSessionId,
            user_message = userMessage
        };

        apiClient.NextTurn(request, OnNextTurnReceived, OnApiError);

        if (userInputField != null)
            userInputField.text = "";

        if (sendButton != null)
            sendButton.interactable = false;
    }

    private void ClearAllPanels()
    {
        foreach (var panel in agentPanels)
        {
            panel.Clear();
        }
    }

    public void RenderMessages(SessionTurnResponse response)
    {
        foreach (var msg in response.messages)
        {
            if (agentPanelMap.TryGetValue(msg.agent_id, out AgentPanelUI panel))
            {
                panel.SetMessage(msg);
            }
            else
            {
                Debug.LogWarning($"No panel found for agent_id: {msg.agent_id}");
            }
        }

        currentSessionId = response.session_id;
        currentTurn = response.turn;

        bool canReply = response.conversation_status == "awaiting_response";

        if (userInputField != null)
            userInputField.interactable = canReply;

        if (sendButton != null)
            sendButton.interactable = canReply;

        Debug.Log($"Rendered turn {currentTurn} for session {currentSessionId}");
        Debug.Log($"Scene: {response.scene}, Status: {response.conversation_status}");
    }

    private void OnSessionStarted(SessionTurnResponse response)
    {
        Debug.Log("Session started successfully.");
        ClearAllPanels();
        RenderMessages(response);
    }

    private void OnNextTurnReceived(SessionTurnResponse response)
    {
        Debug.Log("Next turn received.");
        RenderMessages(response);
    }

    private void OnApiError(string error)
    {
        Debug.LogError($"API Error: {error}");

        if (sendButton != null)
            sendButton.interactable = true;
    }
}